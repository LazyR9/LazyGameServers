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
        self.listeners.append(listener)

    def add_line(self, line):
        self.lines.append(line)
        # Make a copy so changing the original list doesn't break the loop
        for listener in self.listeners[:]:
            listener(line)

    def get_str(self):
        return ''.join(self.lines)

    def print(self):
        print(self.get_str())

# TODO more consistent usage of command vs cmd
class GameServer:

    DEFAULT_STARTUP_CMD = None
    # command to send to console to shutdown server, "^C" means to send a SIGTERM
    DEFAULT_STOP_CMD = "^C"
    # text to look for in the console to know when the server is finished loading
    # if the start_indicator is None, this server doesn't have a way to know when it is done starting.
    # this can also be an empty string to indicate that the status will be set manually, like through a plugin or mod.
    DEFAULT_START_INDICATOR = None
    REPLACEMENTS: dict[str, str] = {}

    def __init__(self, game, startup_command: str, stop_command: str, start_indicator: str, dir):
        self.game = game
        self.startup_command = startup_command if startup_command is not None else self.DEFAULT_STARTUP_CMD
        self.stop_command = stop_command if stop_command is not None else self.DEFAULT_STOP_CMD
        self.start_indicator = start_indicator if start_indicator is not None else self.DEFAULT_START_INDICATOR
        self.directory = dir

        self.process = None
        self.replacements = self.REPLACEMENTS.copy()
        self.status = GameServerStatus.STOPPED

    def get_cmd(self):
        return utils.get_cmd(self.startup_command, self.replacements)

    def start_server(self):
        self.status = GameServerStatus.STARTING if self.start_indicator is not None else GameServerStatus.RUNNING
        self.process = subprocess.Popen(self.get_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.directory)
        self.console = GameConsole()
        if self.start_indicator:
            self.console.add_line_listener(self.find_start_indicator)
        Thread(target=self.read_output, daemon=True).start()
        Thread(target=self.wait_for_stop, daemon=True).start()

    def stop_server(self):
        self.status = GameServerStatus.STOPPING
        if self.stop_command == "^C":
            utils.send_ctrl_c(self.process)
        else:
            self.send_console_command(self.stop_command)

    def send_console_command(self, command):
        if self.status == GameServerStatus.STOPPED:
            return
        self.process.stdin.write(f"{command}\n".encode("utf8"))
        self.process.stdin.flush()

    def read_output(self):
        while self.process.poll() is None:
            line = self.process.stdout.readline().decode("utf8")
            if not line: # an empty line means eof, happens when a program writes eof before actually termainating
                break
            self.console.add_line(line)
        # TODO could a program terminate before writing eof and cause some output to not get captured?
        # seems unlikely but if i encounter problems i'll add some code here to capture left over output
            
    def wait_for_stop(self):
        self.process.wait()
        if self.status != GameServerStatus.STOPPING:
            # TODO better crash handling, probably an auto restart
            print("server crash detected!")
        self.status = GameServerStatus.STOPPED

    def find_start_indicator(self, line):
        if self.start_indicator not in line:
            return
        self.status = GameServerStatus.RUNNING
        self.console.listeners.remove(self.find_start_indicator)
