# collectorbase.py - collector base class XRay reports
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import abc
from abc import abstractmethod, abstractproperty

class Collector(object):
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def __init__(self, repo, **kwargs):
        pass

    @abstractmethod
    def sample(self, chart):
        pass

# Modeline for vim: set tw=79 et ts=4:
