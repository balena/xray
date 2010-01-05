from config import *
import subprocess, os, urllib

def _command(executable, *args):
    params = [executable]+[a for a in args]
    subprocess.check_call(params)

def svnadmin(*args):
    _command('svnadmin', *args)

def svn(*args):
    _command('svn', *args)

def rmdir_rf(dir):
    subprocess.check_call(['rm', '-rf', dir])

def getrepourl(rel_path=''):
    str.strip(rel_path, '/') # remove leading and trailing slashes
    path = os.getcwd() + os.sep + TEMP_REPO
    if len(rel_path):
        rel_path.replace('/', os.sep)
        path += os.sep + rel_path
    return 'file:'+urllib.pathname2url(path)

def getpath(basedir, rel_path):
    str.strip(rel_path, '/') # remove leading and trailing slashes
    path = basedir
    if len(rel_path) and rel_path != '.':
        rel_path.replace('/', os.sep)
        path += os.sep + rel_path
    return path

def gettempdir(rel_path=''):
    return getpath(TEMP_DIR, rel_path)

def getsamplesdir(rel_path=''):
    return getpath(SAMPLES, rel_path)

def getclonedir(rel_path=''):
    return getpath(TEMP_CLONE, rel_path)

def getrepodir(rel_path=''):
    return getpath(TEMP_REPO, rel_path)

