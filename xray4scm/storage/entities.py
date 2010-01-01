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
from datetime import datetime

__all__ = [
'Metadata', 'Author', 'Language', 'File', 'Path', 'FilePath', 'Repository',
'Branch', 'Tag', 'Revision', 'RevisionDetails', 'Module', 'ModuleContent',
'Report', 'DuplicateReport', 'Duplicate', 'BranchFilePath', 'Loc'
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
    duplicateReports = MultipleJoin('DuplicateReport')

    @staticmethod
    def fromExtension(ext):
        # Got from great tool SLOCCount
        extensions = {
            "c":"ansic",
            "ec":"ansic", # Informix C.
            "ecp":"ansic", # Informix C.
            "pgc":"ansic", # Postgres embedded C/C++ (guess C)
            "C":"cpp", "cpp":"cpp", "cxx":"cpp", "cc":"cpp",
            "pcc":"cpp", # Input to Oracle C++ preproc.
            "m":"objc",
            "cs":"cs",
            "c#":"cs",
            # Header files are allocated to the "h" language, and then
            # copied to the correct location later so that C/C++/Objective-C
            # can be separated.
            "h":"h", "H":"h", "hpp":"h", "hh":"h",
            "ada":"ada", "adb":"ada", "ads":"ada",
            "pad":"ada", # Oracle Ada preprocessor.
            "f":"fortran", "F":"fortran", # This catches "wokka.F" as Fortran.
            "f77":"fortran", "F77":"fortran",
            "f90":"f90", "F90":"f90",
            "cob":"cobol", "cbl":"cobol",
            "COB":"cobol", "CBL":"cobol",
            "p":"pascal", "pas":"pascal", "pp":"pascal", "dpr":"pascal",
            "py":"python",
            "s":"asm", "S":"asm", "asm":"asm",
            "sh":"sh", "bash":"sh",
            "csh":"csh", "tcsh":"csh",
            "java":"java",
            "lisp":"lisp", "el":"lisp", "scm":"lisp", "sc":"lisp",
            "lsp":"lisp", "cl":"lisp",
            "jl":"lisp",
            "tcl":"tcl", "tk":"tcl", "itk":"tcl",
            "exp":"exp",
            "pl":"perl", "pm":"perl", "perl":"perl", "ph":"perl",
            "awk":"awk",
            "sed":"sed",
            "y":"yacc",
            "l":"lex",
            "makefile":"makefile",
            "sql":"sql",
            "php":"php", "php3":"php", "php4":"php", "php5":"php",
            "php6":"php",
            "inc":"php", # inc MAY be PHP, but it could be PASCAL too.
            "m3":"modula3", "i3":"modula3",
            "mg":"modula3", "ig":"modula3",
            "ml":"ml", "mli":"ml",
            "mly":"ml",
            "mll":"ml",
            "rb":"ruby",
            "hs":"haskell", "lhs":"haskell",
            "jsp":"jsp", # Java server pages
            "js":"javascript",  # Javascript
            "xml":"xml", # XML
            "html":"xml", # HTML
            "css":"css", # CSS
            "cmake":"cmake", "cmakelists.txt":"cmake", # CMake
            "idl":"idl", # IDL
        }

        if ext[0:0] == '.':
            ext = ext[1:]
        lang = ext in extensions and extensions[ext] or "unknown"
        try:
            l = Language.byLanguage(lang)
        except SQLObjectNotFound as nf:
            l = Language(language=lang)
        except: raise
        return l

class File(SQLObject):
    name = UnicodeCol(length=255, alternateID=True)
    language = ForeignKey('Language', notNone=True, cascade=True)
    paths = MultipleJoin('FilePath')

class Path(SQLObject):
    path = UnicodeCol(length=255, alternateID=True)
    moduleContents = MultipleJoin('ModuleContent')
    files = MultipleJoin('FilePath')

class FilePath(SQLObject):
    file = ForeignKey('File', cascade=True)
    path = ForeignKey('Path', cascade=True)
    filePath = DatabaseIndex(file, path, unique=True)
    duplicates = MultipleJoin('Duplicate')
    branches = MultipleJoin('BranchFilePath')
    revisions = MultipleJoin('Revision')

    @staticmethod
    def breakNames(filepath):
        name = os.path.basename(filepath)
        if name == "": name = '.'
        dir = os.path.dirname(filepath)
        (root, ext) = os.path.splitext(filepath)
        return (dir, name, ext)

    @staticmethod
    def fromFilePath(filepath):
        (dir, name, ext) = FilePath.breakNames(filepath)

        fp = FilePath.select(
                AND(File.q.name == name,
                    Path.q.path == dir),
                join=[INNERJOINOn(Path, FilePath, Path.q.id == FilePath.q.path),
                      INNERJOINOn(None, File, FilePath.q.file == File.q.id)]
        ).getOne(None)

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
                    lang = Language.fromExtension(ext)
                    file = File(name=name, language=lang)
                if path is None:
                    path = Path(path=dir)
                fp = FilePath(file=file, path=path)

        return fp

class Repository(SQLObject):
    url = StringCol(length=255, notNone=True)
    updated = TimestampCol(default=datetime.now(), notNone=True)
    branches = MultipleJoin('Branch')
    modules = MultipleJoin('Module')

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
    tags = MultipleJoin('Tag')
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

    def insertRevision(self, nr, who, msg, date):
        try:
            a = Author.byName(who)
        except SQLObjectNotFound as nf:
            a = Author(name=who)
        except: raise
        try:
            r = Revision.byRevisionBranch(revno=nr, branch=self)
        except SQLObjectNotFound as nf:
            r = Revision(branch=self, revno=nr, author=a, log=msg,
                commitdate=date)
        except: raise
        return r

class Revision(SQLObject):
    revno = IntCol(notNone=True)
    branch = ForeignKey('Branch', notNone=True, cascade=True)
    revnoBranch = DatabaseIndex(revno, branch, unique=True)
    author = ForeignKey('Author', notNone=True, cascade=False)
    log = UnicodeCol(length=600, notNone=True)
    commitdate = TimestampCol(default=datetime.now(), notNone=True)
    details = MultipleJoin('RevisionDetails')

    def insertDetails(self, type, filepath, added, deleted):
        try:
            details = RevisionDetails.byRevisionChangedPath(revision=self,
                    changedpath=filepath)
        except SQLObjectNotFound as nf:
            fp = FilePath.fromFilePath(filepath)
            details = RevisionDetails(revision=self, changedpath=fp,
                changetype=type, linesadded=added, linesdeleted=deleted)
        except: raise
        return details

    @staticmethod
    def byRevisionBranch(revno, branch):
        assert isinstance(branch, Branch)
        assert isinstance(revno, int)
        return Revision.select(
            AND(Revision.q.revno == revno,
                Revision.q.branch == branch)
        ).getOne()

class Tag(SQLObject):
    branch = ForeignKey('Branch', notNone=True, cascade=True)
    name = StringCol(length=45, notNone=True)
    revision = ForeignKey('Revision', cascade=False)
    nameBranch = DatabaseIndex(branch, name, unique=True)

class RevisionDetails(SQLObject):
    revision = ForeignKey('Revision', cascade=True)
    changedpath = ForeignKey('FilePath', cascade=False)
    revisionChangedPath = DatabaseIndex(revision, changedpath, unique=True)
    changetype = EnumCol(enumValues=['A', 'M', 'D'])
    linesadded = IntCol(notNone=True)
    linesdeleted = IntCol(notNone=True)

    @staticmethod
    def byRevisionChangedPath(revision, changedpath):
        (dir, name, ext) = FilePath.breakNames(changedpath)
        return Repository.select(
            AND(File.q.name == name, Path.q.path == dir,
                  RevisionDetails.q.revision == revision),
            join=[INNERJOINOn(Revision, RevisionDetails, Revision.q.id == RevisionDetails.q.revision),
                  INNERJOINOn(None, FilePath, RevisionDetails.q.changedpath == FilePath.q.id),
                  INNERJOINOn(None, File, FilePath.q.file == File.q.id),
                  INNERJOINOn(None, Path, FilePath.q.path == Path.q.id)]
        ).getOne()

class Module(SQLObject):
    repository = ForeignKey('Repository', notNone=True, cascade=False)
    name = StringCol(length=255, alternateID=True)
    description = UnicodeCol(length=600)
    repoName = DatabaseIndex(repository, name, unique=True)
    contents = MultipleJoin('ModuleContent')

class ModuleContent(SQLObject):
    module = ForeignKey('Module', cascade=True)
    path = ForeignKey('Path', cascade=False)
    type = EnumCol(enumValues=['include', 'exclude'])
    modulePath = DatabaseIndex(module, path, unique=True)

class Report(SQLObject):
    reportdate = TimestampCol(default=datetime.now(), notNone=True)
    duplicateReports = MultipleJoin('DuplicateReport')

class DuplicateReport(SQLObject):
    report = ForeignKey('Report', cascade=True)
    language = ForeignKey('Language', cascade=False)
    duplicates = MultipleJoin('Duplicate')
    reportLanguage = DatabaseIndex(report, language, unique=True)

class Duplicate(SQLObject):
    duplicateReport = ForeignKey('DuplicateReport', cascade=True)
    filepath = ForeignKey('FilePath', cascade=True)
    startLine = IntCol(notNone=True)
    endLine = IntCol(notNone=True)

class BranchFilePath(SQLObject):
    filepath = ForeignKey('FilePath', cascade=False)
    branch = ForeignKey('Branch', cascade=True)
    filepathBranch = DatabaseIndex(filepath, branch, unique=True)

class Loc(SQLObject):
    report = ForeignKey('Report', cascade=True)
    filepath = ForeignKey('BranchFilePath', cascade=True)
    reportFilepath = DatabaseIndex(report, filepath, unique=True)
    loc = IntCol(notNone=True)

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

# Modeline for vim: set tw=79 et ts=4:
