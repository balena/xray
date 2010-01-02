# sync.py - synchronize repositories metadata to XRay storage.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import scm, error
from i18n import _
import os, tempfile
import storage

try:
    import ohcount
except ImportError:
    print "Please install ohcount Python extension. For the time this code " \
          "was written, the only available ohcount fork with Python " \
          "extension is located at http://github.com/balena/ohcount."
    raise

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

           ui.write("  %d " % revlog.revno)
           trans = storage.transaction()

           try:
               rev = branch.insertRevision(revlog.revno, revlog.author,
                       revlog.message, revlog.date, connection=trans)

               sourcefiles = {}
               sf_list = ohcount.SourceFileList()
               for fname, chg, added, deleted in revlog.getDiffLineCount(False):
                   details = rev.insertDetails(chg, fname, connection=trans)
                   isfile = chg is not 'D' and \
                            not scminst.isDirectory(revlog.revno, fname, chg) \
                            and not scminst.isBinaryFile(fname, revlog.revno)
                   if isfile:
                       contents = scminst.cat(fname, revlog.revno)
                       (root, ext) = os.path.splitext(fname)
                       (fd, tmppath) = tempfile.mkstemp(ext, 'tmp', dir='./.xray/')
                       file = os.fdopen(fd, 'wb')
                       file.write(contents)
                       file.close()
                       ui.write('.')
                       sf_list.add_file(tmppath)
                       sourcefiles[tmppath] = details

               if len(sourcefiles) > 0:
                   for sf in sf_list:
                       details = sourcefiles.get(sf.filepath)
                       for loc in sf.locs:
                           details.insertLoc(
                               language=loc.language,
                               code=loc.code,
                               comments=loc.comments,
                               blanks=loc.blanks,
                               connection=trans
                           )
                       os.remove(sf.filepath) # remove temp file

           except:
               from glob import glob
               # cleanup temp files
               tmpfiles = glob('./.xray/tmp*')
               for t in tmpfiles:
                   os.remove(t)
               trans.rollback()
               raise

           trans.commit(close=True)
           ui.write('done\n')

       if revlog is None:
           raise error.Abort(_("Up-to-date."))

       ui.write("\n")

