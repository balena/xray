# sync.py - synchronize repositories metadata to XRay storage.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import vcsrouter, error
from i18n import _

def getStartEndRev(vcsclient, branch):
    (startrev, endrev) = vcsclient.findStartEndRev()
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

       vcsclient = vcsrouter.get_instance(repo.url)
       vcsclient.setBranch(branch.name)

       (startrev, endrev) = getStartEndRev(vcsclient, branch)
       if startrev > endrev:
           raise error.Abort("Up-to-date.")

       for revlog in vcsclient.iterrevisions(startrev, endrev):
           if not revlog.isvalid():
               continue

           ui.write(" [%d]" % revlog.revno)
           rev = branch.insertRevision(revlog.revno, revlog.author,
                   revlog.message, revlog.date)
           for fname, chg, added, deleted in revlog.getDiffLineCount(True):
               fname = fname[len('/'+branch.name):]
               if fname == "": fname = '/'
               rev.insertDetails(chg, fname, added, deleted)

       if revlog is None:
           raise error.Abort("Up-to-date.")

       ui.write("\n")

