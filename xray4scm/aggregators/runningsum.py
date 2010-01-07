# running_sum.py - sum of input values
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import aggregatorbase as agg

class RunningSum(agg.Aggregator):

    def __init__(self, **kwargs):
        pass

    def aggregate(self, xdata, ydata):
        last = 0
        for i in xrange(len(xdata)):
            ydata[i] += last
            last = ydata[i]
        return xdata, ydata

# Modeline for vim: set tw=79 et ts=4:
