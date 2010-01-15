# __init__.py - VCS router interface for XRay.
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 3, incorporated herein by reference.

__backends_map__ = {
    'svn': 'xray4scm.scm.svn'
}

def createInstance(identifier, url, **kwargs):
    assert url
    assert identifier

    fromlist = ['Change', 'Client', 'Path', 'Revision']

    impl = None
    if identifier in __backends_map__:
        impl = __import__(__backends_map__[identifier], fromlist=fromlist)
    else:
        return None

    return impl.Client(url, **kwargs)

__all__ = __backends_map__.keys()
