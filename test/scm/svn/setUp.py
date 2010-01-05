from config import *
from framework import *
import os, shutil

def setUp():
    rmdir(TEMP_DIR)
    os.mkdir(TEMP_DIR)

    svnadmin('create', TEMP_REPO)

    for dir in ('/branches', '/tags', '/trunk'):
        svn('mkdir', getrepourl()+dir,
            '-m', 'initial structure')

    cwd = os.getcwd()
    svn('co', getrepourl()+'/trunk', TEMP_CLONE)

    imps = {
        'initial import' : ['ActionscriptFile.as', 'CMakeLists.txt'],
        'foo import'     : ['Makefile', 'Makefile.am', 'TCPSocket.m'],
        'blitz import'   : ['blitzmax.bmx', 'bourne_again_script'],
        'clear fix'      : ['clearsilver_template1.cs', 'configure'],
        'configure bug'  : ['configure.in','core.lisp', 'cs1.cs'],
        'd script fix'   : ['d_script', 'eiffel.e', 'empty.in'],
        'en language'    : ['english.st', 'example.st', 'example.xsl'],
        'foo import 2'   : ['foo.d', 'foo.ebuild', 'foo.eclass'],
        'exheres import' : ['foo.exheres-0', 'foo.exlib', 'foo.glsl'],
        'mk files'       : ['foo.mk', 'foo.pro', 'foo.rb', 'foo.sci'],
        'tex commit'     : ['foo.tex', 'foo.vala', 'foo.vim'],
        'z80 commit'     : ['foo.z80', 'foo_glsl.frag', 'foo_glsl.vert'],
        'big commit'     : ['foo_matlab.m', 'foo_objective_c.h',
                            'foo_objective_c.m', 'foo_octave.m',
                            'foo_upper_case.C', 'foo_upper_case.RB',
                            'fortranfixed.f', 'fortranfree.f', 'frx1.frx',
                            'fs1.fs', 'ocaml.ml', 'perl_w', 'php.inc',
                            'py_script', 'python.data', 'python2.data',
                           ],
        'qmake commit'   : ['qmake.pro', 'ruby_script', 'stratego.str',
                            'structured_basic.b', 't1.m', 't2.m',
                            'upper_case_php', 'uses_cpp_headers.h',
                            'uses_cpp_keywords.h', 'uses_cpp_modeline',
                            'uses_cpp_stdlib_headers.h', 'empty.inc',
                           ],
        'no cpp commit'  : ['uses_no_cpp.h', 'visual_basic.bas',
                            'xml.custom_ext', 'foo.R', 'foo.c',
                           ],
        'rocket files'   : ['foo.cmake', 'bash_script',
                            'classic_basic.b', 'configure.ac',
                             'tcl_script',
                           ],
    }

    for log, files in imps.iteritems():
        for file in files:
            shutil.copy(SAMPLES+os.sep+file, TEMP_CLONE)
            os.chdir(TEMP_CLONE)
            svn('add', file)
            os.chdir(cwd)
        os.chdir(TEMP_CLONE)
        svn('commit', '-m', log)
        os.chdir(cwd)

    exchanges = [
        ('english.st', 'example.st'),
        ('foo.d', 'foo.ebuild'),
        ('foo.exheres-0', 'foo.exlib'),
        ('foo.mk', 'foo.pro'),
        ('foo.rb', 'foo.sci'),
        ('foo.tex', 'foo.vala'),
    ]

    removals = [ 'foo.cmake', 'bash_script' ]

    os.chdir(TEMP_CLONE)
    for a, b in exchanges:
        os.rename(a, a+'.tmp')
        os.rename(b, a)
        os.rename(a+'.tmp', b)
    for removal in removals:
        svn('delete', removal)
    svn('commit', '-m', 'doing some file manipulations')
    os.chdir(cwd)

    rmdir(TEMP_CLONE)

if __name__ == '__main__':
    setUp()
