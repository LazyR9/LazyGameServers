import shlex
import subprocess
import sys
import signal
import os
from threading import Timer
from typing import Any, Callable, ParamSpec, TypeVar

T = TypeVar('T')
P = ParamSpec('P')

is_windows = sys.platform == "win32"

def get_command(command: str, replacements):
    return shlex.split(command.format_map(replacements))

def send_ctrl_c(process: subprocess.Popen):
    """
    Sends a Ctrl-C event if on Windows,
    otherwise just uses `terminate()` to gracefully stop a program
    """
    if is_windows:
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.terminate()

def correct_file_seperator(path: str):
    """
    Replaces any "/" characters in path with the correct OS path seperators.

    :param path: The path to correct file seperators
    :return: A new corrected string
    """
    return os.path.normpath(path)

class RepeatedTimer:
    def __init__(self, interval: int, function: Callable[P, Any], *args: P.args, **kwargs: P.kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            # set as daemon, so that autosave timer doesn't block the program from exiting
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        if self._timer is not None:
            self._timer.cancel()
        self.is_running = False
