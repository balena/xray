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

    def collect(self, branch):
        x, y1, y2, y3 = [], [], [], []
        code, comments, blanks = 0, 0, 0
        for rev in branch.revisions:
            (c_code, c_comments, c_blanks) = rev.getLocDiff()

            code += c_code
            comments += c_comments
            blanks += c_blanks

            x.append(rev.commitdate)
            y1.append(code+comments+blanks)
            y2.append(code+comments)
            y3.append(code)

        self.data = [
            (x, y1, dict(label='blanks',color='#96afd6')),
            (x, y2, dict(label='comments',color='#597db9')),
            (x, y3, dict(label='code',color='#3f5578')),
        ]
        self.mode = 'fill'
        self.format_xdata = mdates.DateFormatter('%b %Y')
        self.xaxis_date = True
        self.output = 'loc-%s.png' % branch.name.replace('/', '-')

# Modeline for vim: set tw=79 et ts=4:
