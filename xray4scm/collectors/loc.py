# loc.py - collects lines of code
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import collectorbase

class Loc(collectorbase.Collector):

    def __init__(self, **kwargs):
        self.code = 'code' in kwargs and kwargs['code'] or False
        self.comments = 'comments' in kwargs and kwargs['comments'] or False
        self.blanks = 'blanks' in kwargs and kwargs['blanks'] or False

    def collect(self, repo):
        x = [ i for i in xrange(1,10) ]
        y1 = [ i*i for i in xrange(1,10) ]
        y2 = [ i*i*i for i in xrange(1,10) ]
        self.data = {
            'data #1': (x,y1),
            'data #2': (x,y2),
        }

# Modeline for vim: set tw=79 et ts=4:
