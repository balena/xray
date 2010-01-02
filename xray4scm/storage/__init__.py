# __init__.py - storage (sql database) for XRay data
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from entities import *
import xray4scm.error as error
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

def getRepositories():
    return list( Repository.select() )

def addRepos(repo_url):
    r = Repository.select(Repository.q.url == repo_url).getOne(None)
    if r:
        raise error.Abort(_("This repository already exists"
                " with id = %d.") % r.id)
    return Repository(url=repo_url)

def addBranch(repo, branch):
    r = Repository.byArg(repo)
    b = Branch.select(AND(Branch.q.repository == r.id,
            Branch.q.name == branch)).getOne(None)
    if b:
        raise error.Abort(_("This branch already exists."))
    b = Branch(repository=r, name=branch)

def rmBranch(repo, branch):
    r = Repository.byArg(repo)
    b = Branch.select(AND(Branch.q.repository == r.id, Branch.q.name == branch)).getOne(None)
    if not b:
        raise error.Abort(_("Branch not found."))
    Branch.delete(b.id)

__backends__= TheURIOpener.schemeBuilders.keys()

# Modeline for vim: set tw=79 et ts=4:
