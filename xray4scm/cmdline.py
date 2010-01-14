# cmdline.py - command line interpreter for XRay.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, sys, errno, shutil
import error, storage
import scm, sync, report
from i18n import _
from ConfigParser import SafeConfigParser
from string import Template

try:
    import cmdln
except ImportError:
    print "Please install cmdln (http://code.google.com/p/cmdln/)"
    raise

alias = cmdln.alias
option = cmdln.option

class CmdLine(cmdln.Cmdln):
    """Usage:
        xray COMMAND [ARGS...]
        xray help COMMAND

    Available commands:
      ${command_list}
      ${help_list}

    Global options:
      global ${option_list}

    XRay is a program for generating grouped statistics from several
    repositories."""
    name = "xray"

    _defaultSqlDb = "sqlite://./.xray/storage.db"

    def __init__(self, ui, *args, **kwargs):
        cmdln.Cmdln.__init__(self, *args, **kwargs)
        cmdln.Cmdln.do_help.aliases.append("h")
        self._config = SafeConfigParser()
        self._ui = ui

    def get_optparser(self):
        """this is the parser for "global" options (not specific to subcommand)"""

        optparser = cmdln.CmdlnOptionParser(self)
        optparser.add_option('--debugger', action='store_true',
                      help='jump into the debugger before executing anything')
        optparser.add_option('--post-mortem', action='store_true',
                      help='jump into the debugger in case of errors')
        optparser.add_option('-t', '--traceback', action='store_true',
                      help='print call trace in case of errors')
        optparser.add_option('-d', '--debug', action='store_true',
                      help='print info useful for debugging')
        optparser.add_option('-v', '--verbose', dest='verbose', action='count', default=0,
                      help='increase verbosity')
        optparser.add_option('-q', '--quiet',   dest='verbose', action='store_const', const=-1,
                      help='be quiet, not verbose')

        return optparser

    # overridden from class Cmdln() to use SCM backends listing
    def _help_preprocess(self, help, cmdname):
        help = cmdln.Cmdln._help_preprocess(self, help, cmdname)
        preprocessors = {
            '${sql_backend_list}': self._help_preprocess_sql_backend_list,
            '${scm_backend_list}': self._help_preprocess_scm_backend_list,
        }
        for marker, preprocessor in preprocessors.items():
            if marker in help:
                help = preprocessor(help, cmdname)
        return help

    def _help_preprocess_sql_backend_list(self, help, cmdname):
        marker = "${sql_backend_list}"
        indent, indent_width = cmdln._get_indent(marker, help)
        suffix = cmdln._get_trailing_whitespace(marker, help)
        block = ', '.join(storage.__backends__)
        help = help.replace(marker, block, 1)
        return help

    def _help_preprocess_scm_backend_list(self, help, cmdname):
        marker = "${scm_backend_list}"
        indent, indent_width = cmdln._get_indent(marker, help)
        suffix = cmdln._get_trailing_whitespace(marker, help)
        block = ', '.join(scm.__all__)
        help = help.replace(marker, block, 1)
        return help

    def _connectToDatabase(self, sqldb):
        if sqldb.startswith('sqlite://.'):
            prefix = os.getcwd()
            prefix = prefix.replace(':', '|')
            prefix = prefix.replace('\\', '/')
            if prefix.startswith('/'):
                prefix = '/'+prefix
            sqldb = sqldb.replace('sqlite://.', 'sqlite:/'+prefix)
        self._sqldb = sqldb
        try:
            connection = storage.connectionForURI(self._sqldb)
        except:
            raise error.Abort(_("Error connecting to"
                    " database %s" % self._sqldb))
        storage.init(connection)

    def _loadConfig(self):
        dest = os.getcwd()
        xraydir = os.path.join(dest, '.xray')
        if not os.path.isdir(xraydir):
            raise error.Abort(_("There is no XRay repository here"
                " ('.xray' not found)"))
        self._config.read(os.path.join(xraydir, 'storage.conf'))
        sqldb = self._config.get('Storage', 'sqldb')
        self._connectToDatabase(sqldb)
        storage.checkVersion()

    @alias('create')
    @option("--db", metavar='SQLDB-URI',
            help="uses an alternative database as storage backend")
    @option("--force", action='store_true',
            help="force the creation of XRay repository")
    def do_init(self, subcmd, opts, *args):
        """${cmd_name}: Create XRay database

        Usage: xray init [DEST]

        Create SQL database and save configurations to the optional
        destination path parameter DEST. If DEST is suppressed, the current
        directory is used to store configurations.

        The format of SQLDB-URI follows SQLObject specification (see option
        '--db' below). If you don't specify anything, sqlite backend will be
        used by default. Some of SQLObject supported URI formats:
  
          * mysql://user:password@host/database
          * mysql://host/database?debug=1
          * postgres://user@host/database?debug=&cache=
          * postgres:///full/path/to/socket/database
          * sqlite:///full/path/to/database
          * sqlite:/C|/full/path/to/database

       Options:
         ${cmd_option_list}"""

        dest = os.getcwd()
        if len(args) == 1:
            dest = args[0]
            if not os.path.exists(dest):
                raise error.Abort(_("'%s' does not exist "
                        "or is an invalid path") % dest)
        elif len(args) > 1:
            raise error.Abort(_('unexpected argument %r') % args[2])

        xraydir = os.path.join(dest, '.xray')
        try:
            os.mkdir(xraydir)
        except OSError as inst:
            if inst.errno == errno.EEXIST:
                if not opts.force:
                    raise error.Abort(_("destination '%s' already exists "
                            "(use '--force' option to overwrite)") % dest)
                else:
                    shutil.rmtree(xraydir)
                    os.mkdir(xraydir)
            else:
                raise

        sqldb = opts.db or self._defaultSqlDb
        self._connectToDatabase(sqldb)
        if storage.checkVersion(None):
            self.stdout.write(_('Found a valid database, '
                    'no tables will be created\n'))
        else:
            storage.create()

        self._config.add_section('Storage')
        self._config.set('Storage', 'sqldb', sqldb)

        with open(os.path.join(xraydir, './storage.conf'), 'wb') as configfile:
            self._config.write(configfile)

    def do_drop(self, subcmd, opts):
        """${cmd_name}: Drop XRay database

        Usage: xray drop

        Drop all tables of a created SQL database. After a drop, you need to create
        the database again if you still need to use the same database.
   
        !!!Use this command with caution.!!!"""

        self._loadConfig()
        storage.drop()

    @alias('clr')
    def do_clear(self, subcmd, opts):
        """${cmd_name}: Clear XRay database

        Usage: xray clear

        Clear all tables of a created SQL database.

        !!!Use this command with caution.!!!"""

        self._loadConfig()
        storage.clear()

    @alias('addr')
    @cmdln.option('--force', action='store_true',
                  help='force addition of the repositories even if they are not available')
    @cmdln.option('--svn-branches-regex', metavar='REGEX',
                  help='informs to svn backend how to interpret branches (defaut: "(/trunk|/branches/[^/]+)")')
    @cmdln.option('--svn-tags-regex', metavar='REGEX',
                  help='informs to svn backend how to interpret tags (defaut: "/tags/[^/]+")')
    def do_addrepos(self, subcmd, opts, scmname, repos):
        """${cmd_name}: Add repositories to be monitored

        Usage: xray addrepos SCM REPOS

        Add repositories to be monitored by XRay.

        Available SCMs: ${scm_backend_list}

        The format of REPOS is dependent of the SCM you are using. Check the
        documentation of the respective SCM for more info on these URLs. Some
        examples:

          $ xray addrepos svn http://domain/path/to/repos
          $ xray addrepos svn file:///path/to/local/repos

        """

        self._loadConfig()
        try:
            scminst = scm.createInstance(scmname, repos, **opts)
            if scminst is None:
                raise error.NotImplementedError(
                    _("No support for this SCM: '%s'") % scmname
                )
        except:
            raise error.Abort(
                ( _("While adding repository %s:\n") +
                  _("Invalid options for this repository.")
                ) % repos
            )
        if not opts.force and not scminst.exists():
            raise error.Abort(
                ( _("While adding repository %s:\n") +
                  _("Invalid repository or access error. "
                    "Please check it and try again.")
                ) % repos
            )

        params = dict(scm=scmname, scmopts=scminst.opts(), url=repos)
        repos = storage.Repository(**params)

    @alias('rmr')
    def do_rmrepos(self, subcmd, opts, scmname, repos):
        """${cmd_name}: Remove repositories from being monitored

        Usage: xray rmrepos SCM REPOS

        Remove repositories from being monitored by XRay. All synchronized data
        available on database will be lost. This action can't be restored, so
        pay attention.

        Example:

          $ xray rmrepos svn http://some.host/some/path"""

        self._loadConfig()
        repos = storage.Repository.byArg(scmname, repos)
        if repos is None:
            raise error.Abort(_("Repository not found."))

        storage.Repository.delete(repos.id)

    @alias('ls', 'l')
    def do_list(self, subcmd, opts, *repos):
        """${cmd_name}: List repositories being monitored

        Usage: xray list
 
        List repositories being monitored by XRay."""

        self._loadConfig()
        for r in storage.Repository.list():
            self._ui.writenl(
                "repo-id:      %d\n"
                "repo-url:     %s\n"
                "updated:      %s\n" %
                (r.id, r.url, r.updated)
            )

            branches = r.branches
            if len(branches) > 0:
                for b in branches:
                    firstrev = b.getFirstRev(0)
                    lastrev = b.getLastRev(0)
                    self._ui.writenl(
                        "branch:       %s\n"
                        "first-revlog: %d\n"
                        "last-revlog:  %d\n" %
                        (b.name, firstrev, lastrev))
 
    @alias('syn', 's')
    def do_sync(self, subcmd, opts, *args):
        """${cmd_name}: Synchronize metadata from repositories

        Usage: xray sync [SCM REPOS]
 
        Synchronize metadata from repositories to XRay database.
 
        If you omit SCM REPOS, all registered repositories will be
        synchronized.

        Examples:
 
          $ xray sync # synchronize all
          $ xray sync svn http://some.host/some/path # only one"""

        self._loadConfig()
        if len(args) == 0:
            repos = storage.Repository.list()
        else:
            repos = [ storage.Repository.byArg(scm=args[0], url=args[1]) ]

        for r in repos:
            try:
                sync.execute(r, self._ui, self.options.verbose)
            except error.Abort as inst:
                self._ui.warn("abort: %s\n" % inst)
            except:
                raise

    @alias('rep', 'r')
    def do_report(self, subcmd, opts, *args):
        """${cmd_name}: Create reports from database

        Usage: xray report [SCM REPOS]
 
        Create reports from XRay database. Only metadata available on
        current database will be used. You may synchronize the database first
        to get most recent changes. For more information about synchronizing
        execute:

          $ xray help sync

       Options:
         ${cmd_option_list}"""

        self._loadConfig()
        if len(args) == 0:
            repos = storage.Repository.list()
        else:
            repos = [ storage.Repository.byArg(scm=args[0], url=args[1]) ]

        for r in repos:
            try:
                report.execute(r, self._ui, self.options.verbose)
            except error.Abort as inst:
                self._ui.warn("abort: %s\n" % inst)
            except:
                raise

# Modeline for vim: set tw=79 et ts=4:
