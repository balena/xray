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
'Branch', 'Tag', 'Revision', 'Change', 'Loc'
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
    scm = StringCol(length=45, notNone=True)
    url = StringCol(length=255, notNone=True)
    scmUrl = DatabaseIndex(scm, url, unique=True)
    scmOpts = PickleCol()
    updated = TimestampCol(default=datetime.now(), notNone=True)

    def __init__(self, *args, **kwargs):
        if 'scm' in kwargs and 'url' in kwargs:
            try:
                r = Repository.byScmUrl(kwargs['scm'], kwargs['url'])
                if r is not None:
                    raise error.Abort(_("This repository already exists"
                            " with id = %d.") % r.id)
            except SQLObjectNotFound as nf:
                pass
            except: raise

        SQLObject.__init__(self, *args, **kwargs)

        class revision_getter:
            def __init__(self, repo):
                self._repo = repo

            def __getitem__(self, key):
                return Revision.select(
                    AND(Repository.q.id == self._repo.id,
                        Revision.q.name == key),
                    join=INNERJOINOn(Revision, Repository,
                            Revision.q.repository == Repository.q.id)
                ).getOne(None)

        self.branch = revision_getter(self)

    def getLastRev(self, default=None):
        return Repository.select(
            Repository.q.id == self.id,
            join=INNERJOINOn(Repository, Revision,
                    Repository.q.id == Revision.q.repository)
        ).max(Revision.q.date) or default

    def markAsUpdated(self):
        self.set(updated=datetime.now())

    def insertRevision(self, revno, author, log, date, connection=None):
        try:
            a = Author.byName(author)
        except SQLObjectNotFound as nf:
            try:
                a = Author(name=author, connection=connection)
            except DuplicateEntryError as inst:
                a = Author.byName(author, connection=connection)
            except: raise
        except: raise

        try:
            r = Revision.byRevisionRepository(revno=revno, repository=self)
        except SQLObjectNotFound as nf:
            try:
                r = Revision(repository=self, revno=revno, author=author,
                        log=log, date=date, connection=connection)
            except DuplicateEntryError as inst:
                r = Revision.byRevisionRepository(revno=revno, repository=self,
                        connection=connection)
            except: raise
        except: raise

        return r

    def branches(self):
        return Branch.select(
            Repository.q.id == repository,
            join=[INNERJOINOn(Revision, Branch,
                    Revision.q.branch == Branch.q.id),
                  INNERJOINOn(None, Repository,
                    Revision.q.repository == Repository.q.id)]
        ).distinct()

    def tags(self):
        return Tag.select(
            Repository.q.id == repository,
            join=[INNERJOINOn(Revision, Tag,
                    Revision.q.tag == Tag.q.id),
                  INNERJOINOn(None, Repository,
                    Revision.q.repository == Repository.q.id)]
        ).distinct()

    def authors(self):
        return Author.select(
            Repository.q.id == repository,
            join=[INNERJOINOn(Revision, Author,
                    Revision.q.author == Author.q.id),
                  INNERJOINOn(None, Repository,
                    Revision.q.repository == Repository.q.id)]
        ).distinct()

    def revisions(self, branch=None, tag=None):
        assert (branch is None and tag is None) or \
               (branch is None and tag is not None) or \
               (branch is not None and tag is None)
        if branch is None and tag is None:
            return list( Revision.select(
                Repository.q.id == self,
                join=[INNERJOINOn(Repository, Revision,
                        Repository.q.id == Revision.q.repository)]
            ) )
        if branch is not None:
            return list( Revision.select(
                AND(Repository.q.id == self,
                    Branch.q.name == branch),
                join=[INNERJOINOn(Repository, Revision,
                        Repository.q.id == Revision.q.repository),
                      INNERJOINOn(None, Change,
                        Revision.q.id == Change.q.revision),
                      INNERJOINOn(None, Branch,
                        Change.q.branch == Branch.q.id)]
            ) )
        if tag is not None:
            return list( Revision.select(
                AND(Repository.q.id == self,
                    Tag.q.name == tag),
                join=[INNERJOINOn(Repository, Revision,
                        Repository.q.id == Revision.q.repository),
                      INNERJOINOn(None, Change,
                        Revision.q.id == Change.q.revision),
                      INNERJOINOn(None, Tag,
                        Change.q.tag == Tag.q.id)]
            ) )

    @staticmethod
    def byScmUrl(scm, url):
        return Repository.select(
            AND(Repository.q.url == url,
                Repository.q.scm == scm)
        ).getOne()

    @staticmethod
    def list():
        return list( Repository.select() )

class Branch(SQLObject):
    name = StringCol(length=255, notNone=True, alternateID=True)
    revisions = MultipleJoin('Revision')

    def selectRevisions(self, repository):
        return Revision.select(
            AND(Branch.q.id == self.id,
                Repository.q.id == repository),
            join=[INNERJOINOn(Revision, Change,
                    Revision.q.id == Change.q.revision),
                  INNERJOINOn(None, Branch,
                    Change.q.branch == Branch.q.id),
                  INNERJOINOn(None, Repository,
                    Revision.q.repository == Repository.q.id)]
        )

    def getFirstRev(self, repository, default=None):
        return self.selectRevisions(repository).min(Revision.q.date) \
            or default

    def getLastRev(self, repository, default=None):
        return self.selectRevisions(repository).max(Revision.q.date) \
            or default

    @staticmethod
    def fromName(name, connection):
        try:
            b = Branch.byName(name)
        except SQLObjectNotFound as nf:
            try:
                b = Branch(name=name, connection=connection)
            except DuplicateEntryError as inst:
                b = Branch.byName(name=name, connection=connection)
            except: raise
        except: raise
        return b

class Tag(SQLObject):
    name = StringCol(length=255, notNone=True, alternateID=True)
    revision = MultipleJoin('Revision')

    def selectRevisions(self, repository):
        return Revision.select(
            AND(Tag.q.id == self.id,
                Repository.q.id == repository),
            join=[INNERJOINOn(Revision, Change,
                    Revision.q.id == Change.q.revision),
                  INNERJOINOn(None, Tag,
                    Change.q.tag == Tag.q.id),
                  INNERJOINOn(None, Repository,
                    Revision.q.repository == Repository.q.id)]
        )

    @staticmethod
    def fromName(name, connection):
        try:
            t = Tag.byName(name)
        except SQLObjectNotFound as nf:
            try:
                t = Tag(name=name, connection=connection)
            except DuplicateEntryError as inst:
                t = Tag.byName(name=name, connection=connection)
            except: raise
        except: raise
        return t

class Revision(SQLObject):
    revno = IntCol(notNone=True)
    repository = ForeignKey('Repository', notNone=True, cascade=True)
    revnoRepos = DatabaseIndex(revno, repository, unique=True)
    author = ForeignKey('Author', notNone=True, cascade=False)
    log = UnicodeCol(length=600, notNone=True)
    date = TimestampCol(default=datetime.now(), notNone=True)
    changes = MultipleJoin('Change')

    @property
    def branches(self):
        return list( Branch.select(
            Revision.q.id == self,
            join=[INNERJOINOn(Revision, Change,
                    Revision.q.id == Change.q.revision),
                  INNERJOINOn(None, Branch,
                    Change.q.branch == Branch.q.id)]
        ) )

    @property
    def tags(self):
        return list( Tag.select(
            Revision.q.id == self,
            join=[INNERJOINOn(Revision, Change,
                    Revision.q.id == Change.q.revision),
                  INNERJOINOn(None, Tag,
                    Change.q.tag == Tag.q.id)]
        ) )

    def insertChange(self, type, filepath, branch, tag, connection=None):
        try:
            change = Change.byRevisionPath(revision=self, path=filepath)
        except SQLObjectNotFound as nf:
            b = branch is not None \
                and Branch.fromName(branch, connection) \
                or None
            t = tag is not None \
                and Tag.fromName(tag, connection) \
                or None
            fp = FilePath.fromFilePath(filepath, connection=connection)
            try:
                change = Change(revision=self, path=fp,
                    changetype=type, branch=b, tag=t, connection=connection)
            except DuplicateEntryError as inst:
                change = Change.byRevisionPath(revision=self,
                        path=filepath, branch=b, tag=t, connection=connection)
            except: raise
        except: raise
        return change

    @staticmethod
    def byRevisionRepository(revno, repository, connection=None):
        assert isinstance(repository, Repository)
        assert isinstance(revno, int)
        return Revision.select(
            AND(Revision.q.revno == revno,
                Revision.q.repository == repository),
            connection=connection
        ).getOne()

    def getLocDiff(self, language=None):
        code, comments, blanks = 0, 0, 0
        for change in self.changes:
            (c_code, c_comments, c_blanks) = change.getLocDiff(self, language)
            code += c_code
            comments += c_comments
            blanks += c_blanks
        return (code, comments, blanks)

class Change(SQLObject):
    revision = ForeignKey('Revision', cascade=True)
    path = ForeignKey('FilePath', cascade=False)
    revisionPath = DatabaseIndex(revision, path, unique=True)
    changetype = EnumCol(enumValues=['A', 'M', 'D', 'R'])
    branch = ForeignKey('Branch', cascade=True)
    tag = ForeignKey('Tag', cascade=True)

    @staticmethod
    def byRevisionPath(revision, path, connection=None):
        (dir, name, ext) = FilePath.breakNames(path)
        return Change.select(
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

    def getLoc(self, language=None):
        if language is None:
            query = Loc.select(
                Change.q.id == self.id,
                join=[INNERJOINOn(Loc, Change, Loc.q.change == Change.q.id)]
            )
        else:
            query = Loc.select(
                AND(Change.q.id == self.id,
                    Language.q.language == language),
                join=[INNERJOINOn(Loc, Change, Loc.q.change == Change.q.id),
                      INNERJOINOn(None, Language, Loc.q.language == Language.q.id)]
            )
        code = query.sum(Loc.q.code)
        comments = query.sum(Loc.q.comments)
        blanks = query.sum(Loc.q.blanks)
        if code is None: code = 0
        if comments is None: comments = 0
        if blanks is None: blanks = 0
        return (code, comments, blanks)

    def getLocDiff(self, revision, language=None):
        code, comments, blanks = self.getLoc(language)
        last_change = Change.select(
            AND(Change.q.path == self.path,
                Revision.q.date < revision.date),
            join=[INNERJOINOn(Change, Revision, Change.q.revision == Revision.q.id)]
        ).limit(1).getOne(None)
        if last_change is None:
            return (code, comments, blanks)
        last_code, last_comments, last_blanks = last_change.getLoc(language)
        return (code-last_code, comments-last_comments, blanks-last_blanks)

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
