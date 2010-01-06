# svn.py - svn backend for XRay.
#
# Copyright (C) 2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import scm
import pysvn, getpass, datetime

class Client(scm.Client):

    def __init__(self, repo_url):
        self._repo_url = repo_url
        self._branch = ''
        self.svnclient = pysvn.Client()
        self._repo_root_url = None

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
        url = self._repo_url
        if len(self._branch) > 0:
            url += '/' + self._branch
        return url

    @property
    def repo_root_url(self):
        if self._repo_root_url is None:
            self._repo_root_url = \
                self.svnclient.root_url_from_path(self._repo_url)
        return self._repo_root_url

    def repo_path(self, path):
        url = self.repo_url
        path = path.lstrip('/')
        if len(path) > 0:
            url += '/' + path
        return url

    def setbranch(self, branch):
        self._branch = branch

    def getrevrange(self):
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

        startrevno, endrevno = 0, 0
        if startrev != None and len(startrev) > 0:
            startrevno = startrev[0].revision.number
            endrevno = headrev.number

        return (startrevno, endrevno)

    def getrev(self, revno):
        revision = self.svnclient.log(
            self.repo_url,
            revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
            revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
            discover_changed_paths=detailedLog,
            limit=1,
        )[0]

        return Revision(revision)

    def cat(self, revno, filepath):
        return self.svnclient.cat(
            self.repo_path(filepath),
            revision=pysvn.Revision(pysvn.opt_revision_kind.number, revno)
        )

    def iterrevs(self, startrev=0, endrev=0, detailedLog=True, cache=1):
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

class Revision(scm.Revision):

    def __init__(self, parent, base):
        self.parent         = parent
        self._author        = base.author
        self._date          = base.date
        self._message       = base.message
        self._revno         = base.revision.number
        self._changed_paths = base.changed_paths

    @property
    def id(self):
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
        for change in self._changed_paths:
            yield Change(self, change)

class Change(scm.Change):

    def __init__(self, parent, base):
        self.parent             = parent
        self._path              = base.path
        self._action            = base.action
        self._copyfrom_path     = base.copyfrom_path

        if base.copyfrom_revision:
            self._copyfrom_revision = base.copyfrom_revision.number
        else:
            self._copyfrom_revision = None

    @property
    def path(self):
        return Path(self, self._path)

    @property
    def changetype(self):
        return self._action

    def iscopy(self):
        return self._copyfrom_path is not None

    def getorigin(self):
        return (self._copyFromPath(), self._copyFromRevision())

    def _copyFromPath(self):
        if self._copyfrom_path is None:
            return None
        return Path(self, self._copyfrom_path)

    def _copyFromRevision(self):
        if self._copyfrom_revision is None:
            return None
        return self._copyfrom_revision

class Path(scm.Path):

    def __init__(self, parent, filepath):
        self.parent    = parent
        self._filepath = filepath

    def isdir(self):
        change = self.parent
        revision = change.parent
        client = revision.parent
        if change.changetype == 'D':
            revno = revision.id-1
        else:
            revno = revision.id
        node = client.svnclient.info2(
            client.repo_path(str(self)),
            revision=pysvn.Revision(pysvn.opt_revision_kind.number, revno),
            recurse=False
        )[0][1]
        return node.kind == pysvn.node_kind.dir

    def isfile(self):
        return not self.isdir()

    def isbinary(self):
        revision = self.parent.parent
        client = revision.parent
        (rev, propdict) = client.svnclient.revproplist(
            client.repo_path(self._filepath),
            pysvn.Revision(pysvn.opt_revision_kind.number, revision.id)
        )
        isbin = False #if explicit mime-type is not found assumes 'text'
        if 'svn:mime-type' in propdict:
            fmimetype = propdict['svn:mime-type']
            if fmimetype.find('text') < 0:
                isbin = True
        return isbin

    def istext(self):
        return not self.isbinary()

    def __str__(self):
        client = self.parent.parent.parent
        filepath = self._filepath.lstrip('/')
        if filepath.startswith(client._branch):
            filepath = filepath.replace(client._branch, '', 1)
            filepath = filepath.lstrip('/')
        return '/'+filepath

# Modeline for vim: set tw=79 et ts=4:
