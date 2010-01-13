# loc.py - collects lines of code
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import collectorbase
import matplotlib.dates as mdates
import datetime

class Loc(collectorbase.Collector):

    def __init__(self, **kwargs):
        self.code = 'code' in kwargs and kwargs['code'] or False
        self.comments = 'comments' in kwargs and kwargs['comments'] or False
        self.blanks = 'blanks' in kwargs and kwargs['blanks'] or False

    def collect(self, repo):
        x = [ datetime.datetime.fromtimestamp(i) for i in xrange(0,11) ]
        y1 = [ i*i for i in xrange(0,11) ]
        y2 = [ 2*i*i for i in xrange(0,11) ]
        y3 = [ 3*i*i for i in xrange(0,11) ]
        self.data = [
            (x, y3, dict(label='blanks',color='#96afd6')),
            (x, y2, dict(label='comments',color='#597db9')),
            (x, y1, dict(label='code',color='#3f5578')),
        ]
        self.mode = 'fill'
        self.format_xdata = mdates.DateFormatter('%b %Y')
        self.xaxis_date = True

# Modeline for vim: set tw=79 et ts=4:
