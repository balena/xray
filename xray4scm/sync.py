# sync.py - synchronize repositories metadata to XRay storage.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import scm, error
from i18n import _

def getStartEndRev(scminst, branch):
    (startrev, endrev) = scminst.findStartEndRev()
    startrev_db = branch.getLastRev()
    if startrev_db is not None:
        startrev = startrev_db+1
    else:
        if startrev == 0 and endrev == 0:
            raise error.Abort(_("There is no revision to sync."))
    return (startrev, endrev)

def execute(repo, ui):
   ui.writenl(_("Synchronizing repo %s...") % repo.url)
   repo.markAsUpdated()

   for branch in repo.branches:
       if branch is None:
           continue

       ui.writenl("  " + _("Branch %s:") % branch.name)

       scminst = scm.createInstance(repo.url)
       scminst.setBranch(branch.name)

       (startrev, endrev) = getStartEndRev(scminst, branch)
       if startrev > endrev:
           raise error.Abort(_("Up-to-date."))

       for revlog in scminst.iterrevisions(startrev, endrev):
           if not revlog.isvalid():
               continue

           ui.write(" [%d]" % revlog.revno)
           rev = branch.insertRevision(revlog.revno, revlog.author,
                   revlog.message, revlog.date)
           for fname, chg, added, deleted in revlog.getDiffLineCount(True):
               fname = fname[len('/'+branch.name):]
               if fname == "": fname = '/'
               rev.insertDetails(chg, fname)
	       # TODO insert Loc counter here

       if revlog is None:
           raise error.Abort(_("Up-to-date."))

       ui.write("\n")

