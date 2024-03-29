import subprocess
from threading import Thread
from typing import Callable
from enum import Enum, auto

from app import utils

# TODO this can support anything that is run through the command line,
# should i be naming everything with "Game"? 

# TODO would states be a better name than status?
class GameServerStatus(Enum):
    STOPPED = 0
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()

class GameConsole:
    def __init__(self):
        self.lines = []
        self.listeners: list[Callable[[str]]] = []

    def add_line_listener(self, listener):
        """
        Adds `listener` to a list of functions to be called when a new line of output is added.
        The only parameter passed is the string that was added.
        """
        self.listeners.append(listener)

    def add_line(self, line):
        self.lines.append(line)
        # Make a copy so changing the original list doesn't break the loop
        for listener in self.listeners[:]:
            listener(line)

    def get_str(self):
        """
        Concatenates all lines of output into one string.
        """
        return ''.join(self.lines)

    def print(self):
        print(self.get_str())

# TODO more consistent usage of command vs cmd
class GameServer:

    # these are defaults for the class, the lowercase versions are instance specific

    # command line command to start server
    DEFAULT_STARTUP_CMD = None
    # command to send to console to shutdown server, "^C" means to send a SIGTERM
    DEFAULT_STOP_CMD = "^C"
    # text to look for in the console to know when the server is finished loading
    # if the start_indicator is None, this server doesn't have a way to know when it is done starting.
    # this can also be an empty string to indicate that the status will be set manually, like through a plugin or mod.
    DEFAULT_START_INDICATOR = None
    REPLACEMENTS: dict[str, str] = {}

    def __init__(self, id, game, storage_manager: StorageManager, startup_command: str = None, stop_command: str = None, start_indicator: str = None, **kwargs):
        self.game = game
        self.storage_manager = storage_manager

        self.startup_command = startup_command if startup_command is not None else self.DEFAULT_STARTUP_CMD
        self.stop_command = stop_command if stop_command is not None else self.DEFAULT_STOP_CMD
        self.start_indicator = start_indicator if start_indicator is not None else self.DEFAULT_START_INDICATOR

        self.process = None
        self.replacements = self.REPLACEMENTS.copy()
        self.status = GameServerStatus.STOPPED

    def get_cmd(self):
        """
        Gets the command for this server.

        Anything in curly braces will get replaced by the corresponding value in `replacements`.
        """
        return utils.get_cmd(self.startup_command, self.replacements)

    def start_server(self):
        """
        Spawns the server subprocess and run threads to monitor it.
        """
        self.status = GameServerStatus.STARTING if self.start_indicator is not None else GameServerStatus.RUNNING
        self.process = subprocess.Popen(self.get_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.get_directory())
        self.console = GameConsole()
        if self.start_indicator:
            self.console.add_line_listener(self._find_start_indicator)
        Thread(target=self._read_output, daemon=True).start()
        Thread(target=self._wait_for_stop, daemon=True).start()

    def stop_server(self):
        self.status = GameServerStatus.STOPPING
        if self.stop_command == "^C":
            utils.send_ctrl_c(self.process)
        else:
            self.send_console_command(self.stop_command)

    def send_console_command(self, command):
        """
        Sends `command` to the stdin of the subprocess, automatically appending a newline
        """
        if self.status == GameServerStatus.STOPPED:
            return
        self.process.stdin.write(f"{command}\n".encode("utf8"))
        self.process.stdin.flush()

    # convenience functions to the StorageManager
    def get_directory(self):
        """
        Gets the directory this server lives in from the storage manager.
        """
        return self.storage_manager.get_server_folder(self)
    
    def get_file(self, file):
        return self.storage_manager.get_file_from_server(self, file)

    def add_shared_file(self, file, bin, game = None, dest_name = None):
        if game is None:
            game = self.game
        self.storage_manager.add_shared_file_to_server(game, bin, file, self, dest_name)

    def remove_shared_file(self, file):
        self.storage_manager.remove_shared_file_from_server(self, file)

    def _read_output(self):
        """
        Constantly monitors the stdout of the subprocess, and adds it to the server's console object.
        Will block until the program exits, only call on another thread.
        """
        while self.process.poll() is None:
            line = self.process.stdout.readline().decode("utf8")
            if not line: # an empty line means eof, happens when a program writes eof before actually termainating
                break
            self.console.add_line(line)
        # TODO could a program terminate before writing eof and cause some output to not get captured?
        # seems unlikely but if i encounter problems i'll add some code here to capture left over output
            
    def _wait_for_stop(self):
        """
        Blocks until the subprocess exits, then sets the status to stopped.
        Also will handle crashes if the server is not set to `STOPPING` when it exits.
        """
        self.process.wait()
        if self.status != GameServerStatus.STOPPING:
            # TODO better crash handling, probably an auto restart
            print("server crash detected!")
        self.status = GameServerStatus.STOPPED

    def _find_start_indicator(self, line):
        """
        Looks for the start indicator in `line`.
        Used as console line listener, and doesn't handle special cases like the indicator being `None` or an empty string.
        """
        if self.start_indicator not in line:
            return
        self.status = GameServerStatus.RUNNING
        self.console.listeners.remove(self._find_start_indicator)
