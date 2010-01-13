# report.py - create XRay reports from available storage.
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import error, storage
from i18n import _
import os, pkgutil
import collectors, aggregators

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
import yaml

class attrdict(dict):

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("attrdict object has no attribute '%s'" % attr)

    def __setattr__(self, attr, value):
        if attr not in self and hasattr(self, attr):
            raise AttributeError("cannot overwrite attribute '%s'" % attr)
        self[attr] = value

    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError:
            raise AttributeError("attrdict object has no attribute '%s'" % attr)

def construct_chart(chart):
    try:
        cls = getattr(collectors, chart.collector)
        chart.collector = cls(**chart)
    except AttributeError:
        raise error.Abort(_("No such collector: %s") % chart.collector)
    if hasattr(chart, 'aggregator') and chart.aggregator is not None:
        try:
            chart.aggregator = getattr(aggregators, chart.aggregator)
        except AttributeError:
            raise error.Abort(_("No such aggregator: %s") % chart.aggregator)
    else:
        chart.aggregator = lambda xdata, ydata: (xdata, ydata)

def get_charts():

    def construct_map(loader, node):
        data = attrdict()
        yield data
        value = loader.construct_mapping(node)
        data.update(value)

    # Create attrdict instances instead of dict instances.
    yaml.add_constructor(u'tag:yaml.org,2002:map', construct_map)

    cfg = pkgutil.get_data('xray4scm', 'charts.yaml')
    charts = yaml.load(cfg)

    for chart in charts:
        construct_chart(chart)

    return charts

def collect_data(charts, repo):
    for chart in charts:
        chart.collector.collect(repo)

def render(charts):
    for i, chart in enumerate(charts):
        collector = chart.collector
        fig = pyplot.figure()
        if 'title' in chart:
            fig.suptitle(chart.title)
        ax = fig.add_subplot(1, 1, 1)
        if 'xlabel' in chart:
            ax.set_xlabel(chart.xlabel)
        if 'ylabel' in chart:
            ax.set_ylabel(chart.ylabel)
        for label, (xdata, ydata) in collector.data.iteritems():
            xdata, ydata = chart.aggregator(xdata, ydata)
            ax.plot(xdata, ydata, chart.get('linestyle', '-'), label=label)
        ax.legend(loc='upper left')
        fig.savefig(chart.get('output', "chart-%d.png" % (i + 1)))

def execute(repo, ui, verbose):
    charts = get_charts()
    collect_data(charts, repo)
    render(charts)

# Modeline for vim: set tw=79 et ts=4:
