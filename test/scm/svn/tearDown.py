from config import *
import subprocess

def rmdir(dir):
    subprocess.check_call(['rm', '-rf', dir])

def rmtest():
    rmdir(TEMP_DIR)

def tearDown():
    rmtest()

if __name__ == '__main__':
    tearDown()
