from config import *
from framework import *
import xray4scm.scm.svn as svn

client = svn.Client(getrepourl())
branches = ['trunk', 'branches/1.0']

print 'Inspecting repository %s' % getrepourl()
for branch in branches:
    print 'Iterating over revisions of branch "%s":' % branch
    client.setbranch(branch)
    (start, end) = client.getrevrange()
    for rev in client.iterrevs(start, end):
        print "------------------------------------------------------------------------------"
        print "%d | %s | %s" % (rev.id, rev.author, rev.date)
        print "%s" % (rev.message)
        for change in rev.iterchanges():
            path = change.path
            print "   %s (dir=%s,bin=%s) %s" % \
                (change.changetype, path.isdir(), path.isbinary(), path)
            print "     (ext=%s,name=%s,namebase=%s,dirname=%s)" % \
                (path.ext, path.name, path.namebase, path.dirname)

