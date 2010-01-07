# entities.py - database entities and operations of XRay data
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, sys
import xray4scm.error as error
from xray4scm.i18n import _
from xray4scm.util import parsedate
from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.dberrors import *
from datetime import datetime

__all__ = [
'Metadata', 'Author', 'Language', 'File', 'Path', 'FilePath', 'Repository',
'Branch', 'Revision', 'Change', 'Loc'
]

class Metadata(SQLObject):
    version = StringCol(length=45, notNone=True)
    created = TimestampCol(default=datetime.now(), notNone=True)
 
class Author(SQLObject):
    name = StringCol(length=255, alternateID=True)
    revisions = MultipleJoin('Revision')

class Language(SQLObject):
    language = StringCol(length=45, alternateID=True)
    files = MultipleJoin('File')

    @staticmethod
    def fromLanguage(lang, connection=None):
        try:
            l = Language.byLanguage(lang)
        except SQLObjectNotFound as nf:
            try:
                l = Language(language=lang, connection=connection)
            except DuplicateEntryError as inst:
                l = Language.byLanguage(lang, connection=connection)
            except: raise
        except: raise
        return l

class File(SQLObject):
    name = UnicodeCol(length=255, alternateID=True)
    paths = MultipleJoin('FilePath')

class Path(SQLObject):
    path = UnicodeCol(length=255, alternateID=True)
    files = MultipleJoin('FilePath')

class FilePath(SQLObject):
    file = ForeignKey('File', cascade=True)
    path = ForeignKey('Path', cascade=True)
    filePath = DatabaseIndex(file, path, unique=True)
    revisions = MultipleJoin('Revision')

    @staticmethod
    def breakNames(filepath):
        name = os.path.basename(filepath)
        if name == "": name = '.'
        dir = os.path.dirname(filepath)
        (root, ext) = os.path.splitext(filepath)
        return (dir, name, ext)

    @staticmethod
    def byFilePath(file, path, connection=None):
        return FilePath.select(
            AND(File.q.name == file,
                Path.q.path == path),
            join=[INNERJOINOn(Path, FilePath, Path.q.id == FilePath.q.path),
                  INNERJOINOn(None, File, FilePath.q.file == File.q.id)],
            connection=connection
        ).getOne(None)

    @staticmethod
    def fromFilePath(filepath, connection=None):
        (dir, name, ext) = FilePath.breakNames(filepath)

        fp = FilePath.byFilePath(name, dir)
        if fp is None:
            try:
                path = Path.byPath(dir)
            except SQLObjectNotFound as nf:
                path = None
            except: raise
            try:
                file = File.byName(name)
            except SQLObjectNotFound as nf:
                file = None
            except: raise

            if file is None or path is None:
                if file is None:
                    try:
                        file = File(name=name, connection=connection)
                    except DuplicateEntryError as inst:
                        file = File.byName(name, connection=connection)
                    except: raise
                if path is None:
                    try:
                        path = Path(path=dir, connection=connection)
                    except DuplicateEntryError as inst:
                        path = Path.byPath(dir, connection=connection)
                    except: raise
                try:
                    fp = FilePath(file=file, path=path, connection=connection)
                except DuplicateEntryError as inst:
                    fp = fp = FilePath.byFilePath(name, dir, connection=connection)
                except: raise

        return fp

class Repository(SQLObject):
    url = StringCol(length=255, notNone=True)
    updated = TimestampCol(default=datetime.now(), notNone=True)
    branches = MultipleJoin('Branch')

    class __branch_getter:
        def __init__(self, repo):
            self._repo = repo

        def __getitem__(self, key):
            return Branch.select(
                AND(Repository.q.id == self._repo.id, Branch.q.name == key),
                join=INNERJOINOn(None, Repository, Branch.q.repository == Repository.q.id)
            ).getOne(None)

    def __init__(self, *args, **kwargs):
        SQLObject.__init__(self, *args, **kwargs)
        self.branch = Repository.__branch_getter(self)

    def getLastRev(self, default=None):
        return Repository.select(
            Repository.q.id == self.id,
            join=[INNERJOINOn(Repository, Branch, Repository.q.id == Branch.q.repository),
                  INNERJOINOn(None, Revision, Branch.q.id == Revision.q.branch)]
        ).max(Revision.q.revno) or default

    def markAsUpdated(self):
        self.set(updated=datetime.now())

    @staticmethod
    def byArg(repo):
        if repo is None: return None
        if isinstance(repo, Repository): return repo
        if repo.isdigit():
            r = Repository.select(Repository.q.id == int(repo)).getOne(None)
        else:
            r = Repository.select(Repository.q.url == repo).getOne(None)
        if not r:
            raise error.Abort(_("This repository does not exist (add with --add-repos)."))
        return r

class Branch(SQLObject):
    repository = ForeignKey('Repository', notNone=True, cascade=True)
    name = StringCol(length=255, notNone=True)
    filePaths = MultipleJoin('FilePath')
    revisions = MultipleJoin('Revision')
    repoName = DatabaseIndex(repository, name, unique=True)

    def getFirstRev(self, default=None):
        return Branch.select(
            Branch.q.id == self.id,
            join=INNERJOINOn(None, Revision, Branch.q.id == Revision.q.branch)
        ).min(Revision.q.revno) or default

    def getLastRev(self, default=None):
        return Branch.select(
            Branch.q.id == self.id,
            join=INNERJOINOn(None, Revision, Branch.q.id == Revision.q.branch)
        ).max(Revision.q.revno) or default

    def insertRevision(self, nr, who, msg, date, connection=None):
        try:
            a = Author.byName(who)
        except SQLObjectNotFound as nf:
            try:
                a = Author(name=who, connection=connection)
            except DuplicateEntryError as inst:
                a = Author.byName(who, connection=connection)
            except: raise
        except: raise
        try:
            r = Revision.byRevisionBranch(revno=nr, branch=self)
        except SQLObjectNotFound as nf:
            try:
                r = Revision(branch=self, revno=nr, author=a, log=msg,
                    commitdate=date, connection=connection)
            except DuplicateEntryError as inst:
                r = Revision.byRevisionBranch(revno=nr, branch=self,
                        connection=connection)
            except: raise
        except: raise
        return r

class Revision(SQLObject):
    revno = IntCol(notNone=True)
    branch = ForeignKey('Branch', notNone=True, cascade=True)
    revnoBranch = DatabaseIndex(revno, branch, unique=True)
    author = ForeignKey('Author', notNone=True, cascade=False)
    log = UnicodeCol(length=600, notNone=True)
    commitdate = TimestampCol(default=datetime.now(), notNone=True)
    changes = MultipleJoin('Change')

    def insertChange(self, type, filepath, connection=None):
        try:
            changes = Change.byRevisionPath(revision=self, path=filepath)
        except SQLObjectNotFound as nf:
            fp = FilePath.fromFilePath(filepath, connection=connection)
            try:
                changes = Change(revision=self, path=fp,
                    changetype=type, connection=connection)
            except DuplicateEntryError as inst:
                changes = Change.byRevisionPath(revision=self,
                        path=filepath, connection=connection)
            except: raise
        except: raise
        return changes

    @staticmethod
    def byRevisionBranch(revno, branch, connection=None):
        assert isinstance(branch, Branch)
        assert isinstance(revno, int)
        return Revision.select(
            AND(Revision.q.revno == revno,
                Revision.q.branch == branch),
            connection=connection
        ).getOne()

class Change(SQLObject):
    revision = ForeignKey('Revision', cascade=True)
    path = ForeignKey('FilePath', cascade=False)
    revisionPath = DatabaseIndex(revision, path, unique=True)
    changetype = EnumCol(enumValues=['A', 'M', 'D', 'R'])

    @staticmethod
    def byRevisionPath(revision, path, connection=None):
        (dir, name, ext) = FilePath.breakNames(path)
        return Repository.select(
            AND(File.q.name == name, Path.q.path == dir,
                  Change.q.revision == revision),
            join=[INNERJOINOn(Revision, Change, Revision.q.id == Change.q.revision),
                  INNERJOINOn(None, FilePath, Change.q.path == FilePath.q.id),
                  INNERJOINOn(None, File, FilePath.q.file == File.q.id),
                  INNERJOINOn(None, Path, FilePath.q.path == Path.q.id)],
            connection=connection
        ).getOne()

    def insertLoc(self, language, code, comments, blanks, connection=None):
        try:
            loc = Loc.byLanguageChange(language, self)
        except SQLObjectNotFound as nf:
            loc = Loc(
                language=Language.fromLanguage(language, connection),
                change=self,
                code=code,
                comments=comments,
                blanks=blanks,
                connection=connection
            )
        except: raise
        return loc

class Loc(SQLObject):
    language = ForeignKey('Language', cascade=True)
    change = ForeignKey('Change', cascade=True)
    languageChange = DatabaseIndex(language, change, unique=True)
    code = IntCol(notNone=True)
    comments = IntCol(notNone=True)
    blanks = IntCol(notNone=True)

    @staticmethod
    def byLanguageChange(language, change):
        language = Language.byLanguage(language)
        return Loc.select(
            AND(Loc.q.language == language,
                Loc.q.change == change)
        ).getOne()

if __name__ == "__main__":
    import pydot

    class Diagram:
        _graph = None
        _models = []
        _relationships = []

        def __init__(self, title='ER_Diagram'):
            self._graph = pydot.Dot(graph_name=title, rankdir='LR')

        def get_graph(self):
            return self._graph;

        def add_model(self, model):
            self._models.append(model)

            # get relationships
            for attrname, attrtype in model.sqlmeta.columns.iteritems():
                if attrtype.foreignKey:
                    self.add_relationship(model, attrname, globals()[attrtype.foreignKey])

        def remove_model(self, model):
            try:
                del self._models[model]
            except IndexError:
                pass

        def add_relationship(self, model, attribute, field):
            self._relationships.append((model, attribute, field))

        def to_string(self):
            self._build()
            return self._graph.to_string()

        def _build(self):
            for model in self._models:
                name = model.__name__
                label = '<<table border="0" cellborder="1" cellpadding="2" cellspacing="0" bgcolor="white">'
                label += '<tr><td bgcolor="#9bab96">%s</td></tr>' % model.__name__
                label += '<tr><td bgcolor="#bed1b8" port="id">id</td></tr>'
                for attr, col in model.sqlmeta.columns.iteritems():
                    if col.alternateID is True:
                        label += '<tr><td bgcolor="#f4f7da" port="%s"><font color="#b9252e">%s</font></td></tr>' % (attr, attr)
                    else:
                        label += '<tr><td bgcolor="#f4f7da" port="%s">%s</td></tr>' % (attr, attr)
                label += '</table>>'
                node = pydot.Node(name=name, label=label, shape='plaintext', fontname="Sans")
                self._graph.add_node(node)

            for model, attribute, field in self._relationships:
                if self._graph.get_node(field.__name__):
                    edge = pydot.Edge(
                        src="%s:%s" % (model.__name__, attribute),
                        dst="%s:id" % field.__name__,
                        minlen='2')
                    arrowhead, arrowtail = self._get_arrow(model, field)
                    edge.set_arrowhead(arrowhead)
                    edge.set_arrowtail(arrowtail)
                    self._graph.add_edge(edge)

        def _get_arrow(self, model, field):
            map = {
                'many'     : 'crow',
                'one'      : 'tee',
                'required' : 'tee',
                'optional' : 'odot',
            }

            cardinality = ('one', 'many')
            modality = ('required', 'optional')
        
            return (map[cardinality[0]] + map[modality[0]],
                    map[cardinality[1]] + map[modality[1]])

    g = Diagram()
    models = []
    for model in __all__:
        klass = globals()[model]
        if issubclass(klass, SQLObject):
            models.append(klass)
    for model in models:
        g.add_model(model)

    open('entities.dot', 'wb').write(g.to_string())

    print "Generated 'entities.dot', now execute 'dot':"
    print "    dot -Tpng -o entities.png entities.dot"

# Modeline for vim: set tw=79 et ts=4:
