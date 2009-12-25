# cmdline.py - command line interpreter for XRay.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, sys, errno, shutil
import error, storage
import vcsrouter, sync
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

    # overridden from class Cmdln() to use VCS backends listing
    def _help_preprocess(self, help, cmdname):
        help = cmdln.Cmdln._help_preprocess(self, help, cmdname)
        preprocessors = {
            '${vcs_backend_list}': self._help_preprocess_vcs_backend_list
        }
        for marker, preprocessor in preprocessors.items():
            if marker in help:
                help = preprocessor(help, cmdname)
        return help

    def _help_preprocess_vcs_backend_list(self, help, cmdname):
        marker = "${vcs_backend_list}"
        indent, indent_width = cmdln._get_indent(marker, help)
        suffix = cmdln._get_trailing_whitespace(marker, help)

        backends = []
        for key, backend in vcsrouter.__backends__.iteritems():
            backends.append('%s* %s: %s' %
                (' '*indent_width, backend['name'], backend['example']))
        block = '\n'.join(backends) + '\n'

        help = help.replace(indent+marker+suffix, block, 1)
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
            self._connection = storage.connectionForURI(self._sqldb)
        except:
            raise error.Abort(_("Error connecting to"
                    " database %s" % self._sqldb))
        self._storage = storage.Storage(self._connection)

    def _loadConfig(self):
        dest = os.getcwd()
        xraydir = os.path.join(dest, '.xray')
        if not os.path.isdir(xraydir):
            raise error.Abort(_("There is no XRay repository here"
                " ('.xray' not found)"))
        self._config.read(os.path.join(xraydir, 'storage.conf'))
        sqldb = self._config.get('Storage', 'sqldb')
        self._connectToDatabase(sqldb)
        self._storage.checkVersion()

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
        if self._storage.checkVersion(None):
            self.stdout.write(_('Found a valid database, '
                    'no tables will be created\n'))
        else:
            self._storage.create()

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
        self._storage.drop()

    @alias('clr')
    def do_clear(self, subcmd, opts):
        """${cmd_name}: Clear XRay database

        Usage: xray clear

        Clear all tables of a created SQL database.

        !!!Use this command with caution.!!!"""

        self._loadConfig()
        self._storage.clear()

    @alias('addr')
    @cmdln.option('--force', action='store_true',
                  help='force addition of the repositories even if they are not available')
    def do_addrepos(self, subcmd, opts, repos, *repos_list):
        """${cmd_name}: Add repositories to be monitored

        Usage: xray addrepos REPOS...

        Add repositories to be monitored by XRay. Note that you need to add
        branches to make monitoring effective (see addbranch command). The format
        for REPOS is like the following:

          ${vcs_backend_list}"""

        self._loadConfig()
        rs = [ repos ]
        rs += [ r for r in repos_list ]
        for r in rs:
            vcsclient = vcsrouter.get_instance(r)
            if not vcsclient:
                self._ui.warn(_("While adding repository %s:\n") % r)
                self._ui.warn("abort: %s\n" %
                    _("There is no support for "
                      "this revision control system yet."))
                continue
            if not opts.force:
                try:
                    (startrev, endrev) = vcsclient.findStartEndRev()
                except:
                    self._ui.warn(_("While adding repository %s:\n") % r)
                    self._ui.warn("abort: %s\n" %
                        _("Invalid repository or access error. "
                          "Please check it and try again."))
                    continue

            repo = self._storage.addRepos(r)
            self._ui.writenl(_("Added repository with id = %d.") % repo.id)

    @alias('rmr')
    def do_rmrepos(self, subcmd, opts, repos, *repos_list):
        """${cmd_name}: Remove repositories from being monitored

        Usage: xray rmrepos REPOS...

        Remove repositories from being monitored by XRay. All current
        available branches will be removed too. This action can't be restored, so pay
        attention.

        You can use the URI format for the repositories or the repository-id.
        Examples:

          $ xray rmrepos svn+http://some.host/some/path
          $ xray rmrepos 10"""

        self._loadConfig()
        rs = [ repos ]
        rs += [ r for r in repos_list ]
        for r in rs:
            try:
                repo = storage.Repository.byArg(r)
            except error.Abort as inst:
                self._ui.warn(_("While removing repository %s:\n") % r)
                self._ui.warn("abort: %s\n" % inst)
                continue
            except: raise

            storage.Repository.delete(repo.id)

    @alias('addb')
    def do_addbranch(self, subcmd, opts, repos, branch, *branch_list):
        """${cmd_name}: Add repository branches to be monitored

        Usage: xray addbranch REPOS BRANCH...
 
        Add branches to be monitored by XRay. Note that only after including
        some branches XRay will actually be able to synchronize metadata.
        
        You can use the URI format of the repository or the repository-id.
        Examples:
        
          $ xray addbranch svn+http://some.host/some/path mybranch
          $ xray addbranch 10 mybranch"""

        self._loadConfig()
        bs = [ branch ]
        bs += [ b for b in branch_list ]
        r = storage.Repository.byArg(repos)
        for b in bs:
            self._storage.addBranch(r, b)
 
    @alias('rmb')
    def do_rmbranch(self, subcmd, opts, repos, branch, *branch_list):
        """${cmd_name}: Remove branches from being monitored

        Usage: xray rmbranch REPOS BRANCH...
 
        Remove branches from being monitored by XRay.

        You can use the URI format of the repository or the repository-id.
        Examples:

          $ xray rmbranch svn+http://some.host/some/path mybranch
          $ xray rmbranch 10 mybranch"""

        self._loadConfig()
        bs = [ branch ]
        bs += [ b for b in branch_list ]
        r = storage.Repository.byArg(repos)
        for b in bs:
            self._storage.rmBranch(r, b)
 
    @alias('ls', 'l')
    def do_list(self, subcmd, opts, *repos):
        """${cmd_name}: List repositories being monitored

        Usage: xray list [OPTIONS] [REPOS]...
 
        List repositories being monitored by XRay.
        
        You can use the URI format of the repository or the repository-id.
        Examples:
        
          $ xray list svn+http://some.host/some/path
          $ xray list 10
 
       Options:
         ${cmd_option_list}"""

        self._loadConfig()
        for r in self._storage.repositories:
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
    def do_sync(self, subcmd, opts, *repos):
        """${cmd_name}: Synchronize metadata from repositories

        Usage: xray sync [REPOS]...
 
        Synchronize metadata from repositories to XRay database.
 
        You can use the URI format of the repository or the repository-id. If
        you do not specify any repository-id, all registered repositories will
        be synchronized.

        Examples:
 
          $ xray sync svn+http://some.host/some/path
          $ xray sync 10"""

        self._loadConfig()
        if len(repos) == 0:
            repos = self._storage.repositories

        for r in repos:
            try:
                sync.execute(r, self._ui)
            except error.Abort as inst:
                self._ui.warn("abort: %s\n" % inst)
            except:
                raise

    @alias('bk')
    def do_backends(self, subcmd, opts):
        """${cmd_name}: List available backends

        Usage: xray backends
 
        List all available XRay backends."""

        self._ui.writenl(_('-- SQL backends:')+' '+
            ', '.join(storage.__backends__))
        self._ui.writenl(_('-- VCS backends:')+' '+
            ', '.join(vcsrouter.__backends__))

    @alias('rep', 'r')
    @option("--all", action='store_true',
            help="report all registered repositories of database")
    def do_report(self, subcmd, opts, *repos):
        """${cmd_name}: Create reports from database

        Usage: xray report [OPTIONS] [REPOS]...
 
        Create reports from XRay database. Only metadata available on
        current database will be used. You would want to synchronize the
        databse first, in this case see the command 'sync'. For more
        information about synchronizing do:

          $ xray help sync

       Options:
         ${cmd_option_list}"""

        self._loadConfig()
        rs = [ repos ]
        rs += [ r for r in repos_list ]
        for r in rs:
            pass

# Modeline for vim: set tw=79 et ts=4:
