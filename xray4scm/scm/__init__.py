# __init__.py - VCS router interface for XRay.
#
# Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

__all__ = [ 'svn' ]

def createInstance(url):
    assert url

    impl = None
    for key in __all__:
        if url.startswith(key+'+') or url.startswith(key+','):
            impl = __import__(key, globals(), locals(), [], -1)
            break
    else:
        raise NotImplementedError("No support for this SCM schema: '%s'" % url)

    return impl.Client(url[len(key)+1:])
