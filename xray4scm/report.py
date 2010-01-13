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
from matplotlib.patches import Rectangle
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

    def attrdict_constructor(loader, node):
        data = attrdict()
        yield data
        value = loader.construct_mapping(node)
        data.update(value)

    # Create attrdict instances instead of dict instances.
    yaml.add_constructor(u'tag:yaml.org,2002:map', attrdict_constructor)

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
            xlabel = chart.xlabel
            if isinstance(xlabel, dict):
                ax.set_xlabel(**xlabel)
            else:
                ax.set_xlabel(xlabel)
        if 'ylabel' in chart:
            ylabel = chart.ylabel
            if isinstance(ylabel, dict):
                ax.set_ylabel(**ylabel)
            else:
                ax.set_ylabel(ylabel)
        if 'xlim' in chart:
            ax.set_xlim(chart.xlim[0], chart.xlim[1])
        if 'ylim' in chart:
            ax.set_ylim(chart.ylim[0], chart.ylim[1])
        if 'xscale' in chart:
            ax.set_xscale(chart.xscale[0], chart.xscale[1])
        if 'yscale' in chart:
            ax.set_yscale(chart.yscale[0], chart.yscale[1])
        if 'grid' in chart:
            ax.grid(chart.grid)

        p, l = [], []
        mode = hasattr(collector, 'mode') and collector.mode or None
        for (xdata, ydata, kwargs) in collector.data:
            xdata, ydata = chart.aggregator(xdata, ydata)
            if mode == 'fill':
                ax.fill_between(xdata, ydata, **kwargs)
            else:
                ax.plot(xdata, ydata, **kwargs)

            if 'label' in kwargs:
                args = {}
                if 'color' in kwargs:
                    args['fc'] = kwargs['color']
                p.append( Rectangle((0, 0), 1, 1, **args) )
                l.append( kwargs['label'] )

        ax.legend(p, l, loc='upper left', ncol=len(p), shadow=True)

        if hasattr(collector, 'format_xdata'):
            ax.xaxis.set_major_formatter(collector.format_xdata)
        if hasattr(collector, 'format_ydata'):
            ax.yaxis.set_major_formatter(collector.format_ydata)
        if hasattr(collector, 'xaxis_date') and collector.xaxis_date:
            fig.autofmt_xdate()
        if hasattr(collector, 'yaxis_date') and collector.yaxis_date:
            fig.autofmt_ydate()

        fig.savefig(chart.get('output', "chart-%d.png" % (i + 1)))

def execute(repo, ui, verbose):
    charts = get_charts()
    collect_data(charts, repo)
    render(charts)

# Modeline for vim: set tw=79 et ts=4:
