from config import *
import subprocess, os, urllib

def _command(executable, *args):
    params = [executable]+[a for a in args]
    subprocess.check_call(params)

def svnadmin(*args):
    _command('svnadmin', *args)

def svn(*args):
    _command('svn', *args)

def rmdir(dir):
    subprocess.check_call(['rm', '-rf', dir])

def getrepourl():
    workdir = os.getcwd() + os.sep + TEMP_REPO
    return 'file:'+urllib.pathname2url(workdir)
