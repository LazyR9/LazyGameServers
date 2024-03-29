import shlex
import subprocess
import sys
import signal
import os

is_windows = sys.platform == "win32"

def get_cmd(cmd: str, replacements):
   return shlex.split(cmd.format_map(replacements))

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
   return os.path.join(*path.split("/"))
