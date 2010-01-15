# svn.py - svn backend for XRay.
#
# Copyright (C) 2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import scmbase
import xray4scm.error as error
import pysvn, getpass, datetime, re

class Client(scmbase.Client):

    def __init__(self, repo_url,
                 svn_branches_regex=r'^(/trunk|/branches/[^/]+)',
                 svn_tags_regex=r'^/tags/[^/]+'):

        self._repo_url = repo_url
        self.svnclient = pysvn.Client()
        self._repo_root_url = None

        self._branches_regex = svn_branches_regex
        self._tags_regex = svn_tags_regex
        self._branches_reobj = re.compile(svn_branches_regex)
        self._tags_reobj = re.compile(svn_tags_regex)

        self.svnclient.callback_get_login = \
            self._get_login
        self.svnclient.callback_ssl_server_trust_prompt = \
            self._ssl_server_trust_prompt
        self.svnclient.callback_ssl_client_cert_password_prompt = \
            self._ssl_client_cert_password_prompt

    def _get_login(self, realm, username, may_save):
        user = raw_input("username for %s: " % realm)
        password = getpass.getpass()
        retcode = user == '' and False or True
        return retcode, user, password, may_save

    def _ssl_server_trust_prompt(self, trust_dict):
        for key, value in trust_dict.items():
            print '%s: %s' % (key, value)
        print ''
        answer = ''
        while answer.lower() not in ['p','t','r']:
            answer = raw_input('(P)ermanent accept, (T)emporary accept or (R)eject: ')
        if answer.lower() == 'p':
            return True, trust_data['failures'], True
        if answer.lower() == 't':
            return True, trust_data['failures'], False
        return False, 0, False

    def _ssl_client_cert_password_prompt(self, realm, may_save):
        certfile = raw_input("client cert for %s: " % realm)
        retcode = certfile == '' and False or True
        return retcode, certfile, may_save

    @property
    def repo_url(self):
        return self._repo_url

    @property
    def repo_root_url(self):
        if self._repo_root_url is None:
            try:
                self._repo_root_url = \
                    self.svnclient.root_url_from_path(self._repo_url)
            except pysvn.ClientError as inst:
                raise error.ScmError(str(inst))
            except: raise
        return self._repo_root_url

    def repo_path(self, path):
        url = self.repo_url
        path = path.lstrip('/')
        if len(path) > 0:
            url += '/' + path
        return url

    def getrevrange(self):
        try:
            headrev = self.svnclient.info2(
                self.repo_url,
                recurse=False
            )[0][1].last_changed_rev

            firstrevdate = self.svnclient.info2(
                self.repo_root_url,
                revision=pysvn.Revision(pysvn.opt_revision_kind.number, 1),
                recurse=False
            )[0][1].last_changed_date

            startrev = self.svnclient.log(
                self.repo_url,
                revision_start=pysvn.Revision(pysvn.opt_revision_kind.date, firstrevdate),
                revision_end=headrev,
                discover_changed_paths=False,
                limit=1
            )
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise

        if startrev == None or len(startrev) == 0:
            return (None, None)

        startrev = Revision(self, startrev[0])
        endrev = Revision(self, self._getrev(headrev.number))
        return (startrev, endrev)

    def exists(self):
        self.getrevrange()
        return True

    def _getrev(self, revno, detailedLog=True):
        try:
            return self.svnclient.log(
                self.repo_url,
                revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
                revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
                discover_changed_paths=detailedLog,
                limit=1,
            )[0]
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise

    def getrev(self, revno, detailedLog=True):
        return Revision(self, self._getrev(revno, detailedLog))

    def opts(self):
        return dict(
            svn_branches_regex = self._branches_regex,
            svn_tags_regex = self._tags_regex
        )

    def iterrevs(self, startrev=0, endrev=0, detailedLog=True, cache=1):
        try:
            while (startrev <= endrev):
                revisions = self.svnclient.log(
                    self.repo_url,
                    revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, startrev),
                    revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, endrev),
                    discover_changed_paths=detailedLog,
                    limit=cache,
                )
                if len(revisions) == 0:
                    break
                startrev = revisions[-1].revision.number+1
                for revision in revisions:
                    yield Revision(self, revision)
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise

class Revision(scmbase.Revision):

    def __init__(self, parent, base):
        self.parent         = parent
        self._date          = base.date
        self._message       = base.message
        self._revno         = base.revision.number
        self._author        = hasattr(base, 'author') \
                          and base.author \
                           or '(no author)'

        # get branches, tags and changes
        self._changes = []
        for change in base.changed_paths:
            (path, branch) = Revision.splitpath(change.path,
                    self.parent._branches_reobj)
            if branch is not None:
                self._changes.append( Change(self, change, path, branch=branch) )
                continue
            (path, tag) = Revision.splitpath(change.path,
                    self.parent._tags_reobj)
            if tag is not None:
                self._changes.append( Change(self, change, path, tag=tag) )
                continue
            self._changes.append( Change(self, change, path) )

    @staticmethod
    def splitpath(path, reobj):
        match = reobj.search(path)
        if match is None:
            return (path, None)
        part = match.group(0)
        path = path.replace(part, '', 1)
        return (path, part)

    @property
    def revno(self):
        return self._revno

    @property
    def author(self):
        return self._author

    @property
    def message(self):
        return self._message

    @property
    def date(self):
        return datetime.datetime.fromtimestamp(self._date)

    def iterchanges(self):
        for change in self._changes:
            yield change

class Change(scmbase.Change):

    def __init__(self, parent, base, path, branch=None, tag=None):
        self.parent             = parent
        self._path              = path
        self._action            = base.action
        self._copyfrom_path     = base.copyfrom_path
        self._branch            = branch
        self._tag               = tag

        if base.copyfrom_revision:
            self._copyfrom_revision = base.copyfrom_revision.number
        else:
            self._copyfrom_revision = None

    @property
    def path(self):
        prefix = self._branch
        if prefix is None:
            prefix = self._tag
        if prefix is None:
            prefix = ''
        return Path(self, self._path, prefix+'/'+self._path)

    @property
    def changetype(self):
        return self._action

    @property
    def branch(self):
        return self._branch

    @property
    def tag(self):
        return self._tag

    def iscopy(self):
        return self._copyfrom_path is not None

    def getorigin(self):
        return (self._copyFromPath(), self._copyFromRevision())

    def cat(self):
        try:
            return self.parent.parent.svnclient.cat(
                self.parent.parent.repo_path(self.path._realpath),
                revision=pysvn.Revision(pysvn.opt_revision_kind.number,
                            self.parent.revno)
            )
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise

    def _copyFromPath(self):
        if self._copyfrom_path is None:
            return None
        return Path(self, self._copyfrom_path)

    def _copyFromRevision(self):
        if self._copyfrom_revision is None:
            return None
        return self._copyfrom_revision

class Path(scmbase.Path):

    def __init__(self, parent, filepath, realpath):
        self.parent    = parent
        self._filepath = filepath
        self._realpath = realpath

    def isdir(self):
        change = self.parent
        revision = change.parent
        client = revision.parent
        if change.changetype == 'D':
            revno = revision.revno-1
        else:
            revno = revision.revno
        try:
            node = client.svnclient.info2(
                client.repo_path(self._realpath),
                revision=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
                recurse=False
            )[0][1]
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise
        return node.kind == pysvn.node_kind.dir

    def isfile(self):
        return not self.isdir()

    def isbinary(self):
        revision = self.parent.parent
        client = revision.parent
        try:
            (rev, propdict) = client.svnclient.revproplist(
                client.repo_path(self._realpath),
                pysvn.Revision(pysvn.opt_revision_kind.number, revision.revno)
            )
        except pysvn.ClientError as inst:
            raise error.ScmError(str(inst))
        except: raise
        isbin = False #if explicit mime-type is not found assumes 'text'
        if 'svn:mime-type' in propdict:
            fmimetype = propdict['svn:mime-type']
            if fmimetype.find('text') < 0:
                isbin = True
        return isbin

    def istext(self):
        return not self.isbinary()

    def __str__(self):
        return self._filepath

# Modeline for vim: set tw=79 et ts=4:
