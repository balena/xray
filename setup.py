#!/usr/bin/env python

from distutils.core import setup
import distutils.command.build
import distutils.command.install_data
import os.path
import xray.core
import sys

# optional support for py2exe
try:
    import py2exe
    HAVE_PY2EXE = True
except:
    HAVE_PY2EXE = False

addparams = {}
if HAVE_PY2EXE:
    addparams['console'] = [{'script': 'xray.py', 'dest_base': 'xray'}]
    addparams['zipfile'] = 'shared.lib'
    addparams['options'] = {
        'py2exe': {
            'optimize': 0,
            'compressed': True,
            'packages': ['pysvn', 'cmdln', 'SQLObject', 'StringIO', 'gzip']
        }
    }

setup(
    name='xray',
    version = xray.core.__version__,
    description = 'XRay: Coding Analysis for SCMs',
    long_description =
        'XRay is an analysis tool built upon your SCMs, aimed to '
        'consolidade project statistics from many repositories at the same '
        'time, generating code reports and development statistics from '
        'your repository log data.',
    author = 'Guilherme Balena Versiani',
    author_email = 'guibv@comunip.com.br',
    license = 'GPL',
    platforms = ['Linux','Mac OSX','Windows XP/2000/NT','Windows 95/98/ME'],
    keywords = ['x-ray', 'coding', 'analysis', 'scm', 'svn', 'hg'],
    url = 'http://xray.sourceforge.net/',
    download_url = 'http://sourceforge.net/projects/xray/files/',
    packages = ['xray'],
    scripts = ['xray.py'],
    **addparams
)
