# __init__.py - VCS router interface for XRay.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

__all__ = [ 'svn' ]

def createInstance(identifier, url):
    assert url
    assert identifier

    impl = None
    for key in __all__:
        if identifier == key:
            impl = __import__(key)
            break
    else:
        return None

    return impl.Client(url)
