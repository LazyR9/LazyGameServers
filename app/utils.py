import shlex
import subprocess
import sys
import signal

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
