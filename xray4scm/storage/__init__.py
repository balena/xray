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

__all__ = [
'Metadata', 'Author', 'Language', 'File', 'Path', 'FilePath', 'Repository',
'Branch', 'Tag', 'Revision', 'RevisionDetails', 'Module', 'ModuleContent',
'Report', 'DuplicateReport', 'Duplicate', 'BranchFilePath', 'Loc', 'Storage',
'connectionForURI'
]

class Storage(object):
    """
    Storage base class for storage that uses the SQLObject wrappers.
    This offers the convenience of simply having to declare the SQLObject
    classes as a class variable and their connection gets initialized
    automatically.
    """

    _sqlobject_classes = [
        Metadata,
        Author,
        Language,
        File,
        Path,
        FilePath,
        Repository,
        Branch,
        Tag,
        Revision,
        RevisionDetails,
        Module,
        ModuleContent,
        Report,
        DuplicateReport,
        Duplicate,
        BranchFilePath,
        Loc
    ]

    def __init__(self, connection):
        assert self._sqlobject_classes
        for cls in self._sqlobject_classes:
            cls._connection = connection

    def _defineVersion(self):
        m = Metadata(version=1)

    def create(self):
        """Checks if database tables exist and if they don't, creates them."""
        for cls in self._sqlobject_classes:
            cls.createTable(ifNotExists=True)
        Metadata.clearTable()
        self._defineVersion()

    def clear(self):
        """Clears the entries/tables."""
        for cls in self._sqlobject_classes:
            cls.dropTable()
            cls.createTable()
        self._defineVersion()

    def drop(self):
        """Drops all database tables."""
        for cls in self._sqlobject_classes:
            cls.dropTable()

    def checkVersion(self, e=error.Abort(_('Invalid database version'))):
        try:
            res = Metadata.select(Metadata.q.version == 1).count() == 1
        except:
            if e: raise e
            return False
        if not res and e:
            raise e
        return res

    def __getattr__(self, name):
        if name == 'repositories':
            return list( Repository.select() )

    def addRepos(self, repo_url):
        r = Repository.select(Repository.q.url == repo_url).getOne(None)
        if r:
            raise error.Abort(_("This repository already exists"
                    " with id = %d.") % r.id)
        return Repository(url=repo_url)

    def addBranch(self, repo, branch):
        r = Repository.byArg(repo)
        b = Branch.select(AND(Branch.q.repository == r.id,
                Branch.q.name == branch)).getOne(None)
        if b:
            raise error.Abort(_("This branch already exists."))
        b = Branch(repository=r, name=branch)

    def rmBranch(self, repo, branch):
        r = Repository.byArg(repo)
        b = Branch.select(AND(Branch.q.repository == r.id, Branch.q.name == branch)).getOne(None)
        if not b:
            raise error.Abort(_("Branch not found."))
        Branch.delete(b.id)

__backends__= TheURIOpener.schemeBuilders.keys()

# Modeline for vim: set tw=79 et ts=4:
