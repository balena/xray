# vcsrouter.py - VCS router interface for XRay.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

def get_svn_instance(url):
    from svnlogiter import SVNLogClient
    return SVNLogClient(url)

__backends__ = {
    'svn' : {
        'name'    : 'Subversion',
        'factory' : get_svn_instance,
        'example' : 'svn+http://some.host/some/path'
    }
}

def get_instance(url):
    assert url
    desc = None
    for key, desc in __backends__.iteritems():
        if url.startswith(key+'+') or url.startswith(key+','):
            break
        desc = None
    if not desc:
        return None
    return desc['factory']( url[len(key)+1:] )
