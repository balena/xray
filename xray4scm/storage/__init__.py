# __init__.py - storage (sql database) for XRay data
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from entities import *
import xray4scm.error as error
import pickle
from xray4scm.i18n import _
from sqlobject import connectionForURI
from sqlobject.sqlbuilder import *
from sqlobject.dbconnection import TheURIOpener

__all__ = entities.__all__ + [ 'Storage', 'connectionForURI' ]

_connection = None

def init(connection):
    for cls in entities.__all__:
        globals()[cls]._connection = connection
    globals()['_connection'] = connection

def transaction():
    return globals()['_connection'].transaction()

def _defineVersion():
    m = Metadata(version=1)

def create():
    """Checks if database tables exist and if they don't, creates them."""
    for cls in entities.__all__:
        globals()[cls].createTable(ifNotExists=True)
    Metadata.clearTable()
    _defineVersion()

def clear():
    """Clears the entries/tables."""
    for cls in entities.__all__:
        globals()[cls].dropTable()
        globals()[cls].createTable()
    _defineVersion()

def drop():
    """Drops all database tables."""
    for cls in entities.__all__:
        globals()[cls].dropTable()

def checkVersion(e=error.Abort(_('Invalid database version'))):
    try:
        res = Metadata.select(Metadata.q.version == 1).count() == 1
    except:
        if e: raise e
        return False
    if not res and e:
        raise e
    return res

__backends__= TheURIOpener.schemeBuilders.keys()

# Modeline for vim: set tw=79 et ts=4:
