# scmbase.py - scm base class for XRay
#
# Copyright (C) 2009-2010 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import abc
import os.path
from abc import abstractmethod, abstractproperty

class Client(object):
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def setbranch(self, branch):
        pass

    @abstractmethod
    def getrevrange(self):
        pass

    @abstractmethod
    def getrev(self, rev_id):
        pass

    @abstractmethod
    def cat(self, rev_id, path):
        pass

    @abstractmethod
    def iterrevs(self, startrev=0, endrev=0):
        pass

class Revision(object):
    __metaclass__ = abc.ABCMeta

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def author(self):
        pass

    @abstractproperty
    def message(self):
        pass

    @abstractproperty
    def date(self):
        pass
        
    @abstractproperty
    def tag(self):
        pass

    @abstractproperty
    def branch(self):
        pass

    @abstractmethod
    def iterchanges(self):
        pass

class Change(object):
    __metaclass__ = abc.ABCMeta

    @abstractproperty
    def path(self):
        pass

    @abstractproperty
    def changetype(self):
        pass

    @abstractmethod
    def iscopy(self):
        pass

    @abstractmethod
    def getorigin(self):
        pass

class Path(object):
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def isdir(self):
        pass

    @abstractmethod
    def isfile(self):
        pass

    @abstractmethod
    def isbinary(self):
        pass

    @abstractmethod
    def istext(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @property
    def ext(self):
        (root, ext) = os.path.splitext(str(self))
        return ext

    @property
    def name(self):
        (root, name) = os.path.split(str(self))
        return name

    @property
    def namebase(self):
        (root, ext) = os.path.splitext(self.name)
        return root

    @property
    def dirname(self):
        (root, name) = os.path.split(str(self))
        return root

# Modeline for vim: set tw=79 et ts=4:
