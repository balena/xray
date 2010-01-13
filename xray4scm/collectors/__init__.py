# __init__.py - collectors (from storage) for XRay charts
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

collectors={
    'xray4scm.collectors.loc': ['Loc'],
}

__all__ = []
for name, fromlist in collectors.iteritems():
    imp = __import__(name, fromlist=fromlist)
    for f in fromlist:
        globals()[f] = getattr(imp, f)
        __all__.append(f)

# Modeline for vim: set tw=79 et ts=4:
