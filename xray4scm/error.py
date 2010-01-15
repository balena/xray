# error.py - XRay exceptions
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

"""XRay exceptions."""

# derived from KeyboardInterrupt to simplify some breakout code
class SignalInterrupt(KeyboardInterrupt):
    """Exception raised on SIGTERM and SIGHUP."""

class Abort(Exception):
    """Raised if a command needs to print an error and exit."""

class ScmError(Exception):
    """Raised when some SCM error occurs."""

# Modeline for vim: set tw=79 et ts=4:
