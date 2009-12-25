# dispatch.py - dispatch XRay commands from the command line
#
# Original author: Copyright 2005, 2006 Matt Mackall <mpm@selenic.com>
# Modified by: Copyright (C) 2009 Guilherme Versiani <guibv@comunip.com.br>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import sys, signal
import error
from i18n import _
import ui as _ui

def run():
    "run the command in sys.argv"
    sys.exit( dispatch(sys.argv[:]) )

def dispatch(args):
    "run the command specified in args"
    try:
        u = _ui.ui()
        if '--traceback' in args:
            u.setconfig('ui', 'traceback', 'on')
    except error.Abort as inst:
        sys.stderr.write(_("abort: %s\n") % inst)
        return -1
    except error.ConfigError as inst:
        sys.stderr.write(_("xray: %s\n") % inst)
        return -1
    return _runcatch(u, args)

def _runcatch(ui, args):
    def catchterm(*args):
        raise error.SignalInterrupt

    for name in 'SIGBREAK', 'SIGHUP', 'SIGTERM':
        num = getattr(signal, name, None)
        if num: signal.signal(num, catchterm)

    try:
        try:
            # enter the debugger before command execution
            if '--debugger' in args:
                pdb.set_trace()
            try:
                return _dispatch(ui, args)
            finally:
                ui.flush()
        except:
            # enter the debugger when we hit an exception
            if '--debugger' in args:
                pdb.post_mortem(sys.exc_info()[2])
            ui.traceback()
            raise

    # Global exception handling, alphabetically
    # XRay-specific first, followed by built-in and library exceptions
    except error.Abort as inst:
        ui.warn("abort: %s\n" % inst)
        return -1
    except error.SignalInterrupt:
        ui.warn(_("killed!\n"))
    except ImportError, inst:
        m = str(inst).split()[-1]
        ui.warn(_("abort: could not import module %s!\n") % m)
    except IOError, inst:
        if hasattr(inst, "code"):
            ui.warn(_("abort: %s\n") % inst)
        elif hasattr(inst, "reason"):
            try: # usually it is in the form (errno, strerror)
                reason = inst.reason.args[1]
            except: # it might be anything, for example a string
                reason = inst.reason
            ui.warn(_("abort: error: %s\n") % reason)
        elif hasattr(inst, "args") and inst.args[0] == errno.EPIPE:
            if ui.debugflag:
                ui.warn(_("broken pipe\n"))
        elif getattr(inst, "strerror", None):
            if getattr(inst, "filename", None):
                ui.warn(_("abort: %s: %s\n") % (inst.strerror, inst.filename))
            else:
                ui.warn(_("abort: %s\n") % inst.strerror)
        else:
            raise
    except OSError, inst:
        if getattr(inst, "filename", None):
            ui.warn(_("abort: %s: %s\n") % (inst.strerror, inst.filename))
        else:
            ui.warn(_("abort: %s\n") % inst.strerror)
    except KeyboardInterrupt:
        try:
            ui.warn(_("interrupted!\n"))
        except IOError, inst:
            if inst.errno == errno.EPIPE:
                if ui.debugflag:
                    ui.warn(_("\nbroken pipe\n"))
            else:
                raise
    except MemoryError:
        ui.warn(_("abort: out of memory\n"))
    except SystemExit, inst:
        # Commands shouldn't sys.exit directly, but give a return code.
        # Just in case catch this and and pass exit code to caller.
        return inst.code
    except:
        ui.warn(_("** unknown exception encountered, details follow\n"))
        ui.warn(_("** report bug details to the author\n"))
        ui.warn(_("Unexpected error: %s") % sys.exc_info()[0])
        raise

    return -1

def _dispatch(_ui, args):
    from cmdline import CmdLine
    xray = CmdLine(ui=_ui)
    xray.main(args)

# Modeline for vim: set tw=79 et ts=4:
