# ui.py - user interface bits for XRay
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from i18n import _
import errno, os, sys, tempfile, traceback
import error

class ui(object):
    def __init__(self):
        self._buffers = []
        self.quiet = self.verbose = self.debugflag = self.tracebackflag = False
        self._reportuntrusted = True

    def copy(self):
        return self.__class__(self)

    def setconfig(self, section, name, value):
        pass

    def write(self, *args):
        for a in args:
            sys.stdout.write(str(a))

    def writenl(self, *args):
        for a in args:
            sys.stdout.write(str(a)+'\n')

    def write_err(self, *args):
        try:
            if not sys.stdout.closed: sys.stdout.flush()
            for a in args:
                sys.stderr.write(str(a))
            # stderr may be buffered under win32 when redirected to files,
            # including stdout.
            if not sys.stderr.closed: sys.stderr.flush()
        except IOError, inst:
            if inst.errno != errno.EPIPE:
                raise

    def flush(self):
        try: sys.stdout.flush()
        except: pass
        try: sys.stderr.flush()
        except: pass

    def status(self, *msg):
        if not self.quiet: self.write(*msg)

    def warn(self, *msg):
        self.write_err(*msg)

    def note(self, *msg):
        if self.verbose: self.write(*msg)

    def debug(self, *msg):
        if self.debugflag: self.write(*msg)

    def traceback(self, exc=None):
        '''print exception traceback if traceback printing enabled.
        only to call in exception handler. returns true if traceback
        printed.'''
        if self.tracebackflag:
            if exc:
                traceback.print_exception(exc[0], exc[1], exc[2])
            else:
                traceback.print_exc()
        return self.tracebackflag

    def progress(self, topic, pos, item="", unit="", total=None):
        '''show a progress message

        With stock hg, this is simply a debug message that is hidden
        by default, but with extensions or GUI tools it may be
        visible. 'topic' is the current operation, 'item' is a
        non-numeric marker of the current position (ie the currently
        in-process file), 'pos' is the current numeric position (ie
        revision, bytes, etc.), unit is a corresponding unit label,
        and total is the highest expected pos.

        Multiple nested topics may be active at a time. All topics
        should be marked closed by setting pos to None at termination.
        '''

        if pos == None or not self.debugflag:
            return

        if unit:
            unit = ' ' + unit
        if item:
            item = ' ' + item

        if total:
            pct = 100.0 * pos / total
            self.debug('%s:%s %s/%s%s (%4.2g%%)\n'
                     % (topic, item, pos, total, unit, pct))
        else:
            self.debug('%s:%s %s%s\n' % (topic, item, pos, unit))
