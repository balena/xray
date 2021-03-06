XRay -- Coding Analysis for SCMs
================================


Patches can be submitted via:

- preferrably creating an account at Bitbucket and forking
  [xray project](http://bitbucket.org/balena/xray/).
- [Sourceforge bugtracking](https://sourceforge.net/projects/xray/).
- mail patches to guibv att comunip.com.br
- or work directly on hg, if you got write access
  ssh://xray.hg.sourceforge.net/hgroot/xray/xray


Requirements:
-------------

- cmdln >= 1.1.2
- SQLObject >= 0.12.0
- pysvn for support to SVN repositories
- ohcount >= 3.0.0 with Python extension
  available at http://github.com/balena/ohcount


Installation:
-------------

To install from hg or from source package, do:

    python setup.py build
    python setup.py install


Usage:
------

To create a new XRay base, you will need a new empty directory:

    $ mkdir repos
    $ cd repos
    $ xray init

It is possible to delegate database operations to a centralized one:

    $ xray init --db=mysql://user:password@host/database 

Then, you add a bunch of repositories and branches:

    $ xray addrepos svn+http://some.domain/path/to/repos
    $ xray addbranch svn+http://some.domain/path/to/repos trunk branches/1.0

Now it is time to get things in sync (take a time to a coffee):

    $ xray sync

If you want to update just one repository, do:

    $ xray sync svn+http://some.domain/path/to/repos

Whenever you need to create reports, do:

    $ xray report

Have fun!


Authors:
--------
Guilherme Balena Versiani - guibv at comunip.com.br
