# sync.py - synchronize repositories metadata to XRay storage.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import scm, error, storage
from i18n import _
import os

try:
    import ohcount
except ImportError:
    print "Please install ohcount Python extension. For the time this code " \
          "was written, the only available ohcount fork with Python " \
          "extension is located at http://github.com/balena/ohcount."
    raise

class Sync(object):

    def __init__(self, repo, ui, verbose):
        self.repo    = repo
        self.ui      = ui
        self.verbose = verbose

    def process(self):
        self.ui.writenl(_("Synchronizing repo %s...") % self.repo.url)
        for branch in self.repo.branches:
            try:
                SyncBranch(self, branch).process()
            except error.Abort as inst:
                self.ui.warn('abort: %s\n' % inst)
                continue
            except: raise
        self.repo.markAsUpdated()

class SyncBranch(object):

    def __init__(self, parent, branch):
        self.parent  = parent
        self.ui      = parent.ui
        self.verbose = parent.verbose
        self.branch  = branch
        self.scminst = scm.createInstance(parent.repo.url)
        self.scminst.setbranch(branch.name)

    def getrevrange(self):
        (startrev, endrev) = self.scminst.getrevrange()
        if startrev != 0 and endrev != 0:
            dbstartrev = self.branch.getLastRev()
            if dbstartrev is not None:
                startrev = dbstartrev+1
        return (startrev, endrev)

    def process(self):
        self.ui.writenl("  " + _("Branch %s:") % self.branch.name)
        (startrev, endrev) = self.getrevrange()
        if startrev == 0 and endrev == 0:
            raise error.Abort(_("There is no revision available to sync yet."))
        if startrev > endrev:
            raise error.Abort(_("Up-to-date."))
        for scmrev in self.scminst.iterrevs(startrev, endrev):
            SyncRevision(self, scmrev).process()
        if scmrev is None:
            raise error.Abort(_("Up-to-date."))

class SyncRevision(object):

    def __init__(self, parent, scmrev):
        self.parent      = parent
        self.ui          = parent.ui
        self.verbose     = parent.verbose
        self.scmrev      = scmrev

    def process(self):
        if self.verbose == 1:
            self.ui.writenl('--- Revision %d ---' % self.scmrev.id)
            self.ui.flush()
        else:
            self.ui.write("  %d " % self.scmrev.id)
            self.ui.flush()

        self.trans = storage.transaction()
        self.storrev = self.parent.branch.insertRevision(
            self.scmrev.id,
            self.scmrev.author,
            self.scmrev.message,
            self.scmrev.date,
            connection=self.trans
        )

        try:
            for change in self.scmrev.iterchanges():
                SyncChange(self, change).process()
        except:
            self.trans.rollback()
            raise

        self.trans.commit(close=True)

        if self.verbose != 1:
            self.ui.writenl('done')
            self.ui.flush()

class SyncChange(object):

    def __init__(self, parent, change):
        self.parent  = parent
        self.ui      = parent.ui
        self.verbose = parent.verbose
        self.change  = change

    def process(self):
        path = self.change.path

        if self.verbose == 1:
            self.ui.writenl('  %s %s' % (self.change.changetype, path))
            self.ui.flush()

        details = self.parent.storrev.insertChange(
            self.change.changetype, str(path), connection=self.parent.trans)

        if self.change.changetype == 'D' or self.change.changetype == 'R':
            return
        if path.isdir():
            return
        if path.isbinary():
            return

        contents = self.parent.parent.scminst.cat(
            self.parent.scmrev.id, str(path))

        sf = ohcount.SourceFile(filename=str(path), contents=contents)
        for loc in sf.locs:
            details.insertLoc(
                language=loc.language,
                code=loc.code,
                comments=loc.comments,
                blanks=loc.blanks,
                connection=self.parent.trans
            )
            if self.verbose == 1:
                self.ui.writenl('    (lang=%s,code=%d,comments=%d,blanks=%d)'%\
                    (loc.language, loc.code, loc.comments, loc.blanks))
                self.ui.flush()

        if self.verbose != 1:
            self.ui.write('.')
            self.ui.flush()

def execute(repo, ui, verbose):
    Sync(repo, ui, verbose).process()

# Modeline for vim: set tw=79 et ts=4:
