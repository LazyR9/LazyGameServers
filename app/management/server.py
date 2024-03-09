import subprocess
from threading import Thread
from typing import Callable

from app import utils

# TODO this can support anything that is run through the command line,
# should i be naming everything with "Game"? 
class GameConsole:
    def __init__(self):
        self.lines = []
        self.listeners: list[Callable[[str]]] = []

    def add_line_listener(self, listener):
        self.listeners.append(listener)

    def add_line(self, line):
        self.lines.append(line)
        for listener in self.listeners:
            listener(line)

    def get_str(self):
        return ''.join(self.lines)

    def print(self):
        print(self.get_str())

# TODO more consistent usage of command vs cmd
class GameServer:

    DEFAULT_STARTUP_CMD = None
    REPLACEMENTS: dict[str, str] = {}

    def __init__(self, game, startup_command: str, dir):
        self.game = game
        self.startup_command = startup_command if startup_command is not None else self.DEFAULT_STARTUP_CMD
        self.directory = dir
        self.process = None
        self.replacements = self.REPLACEMENTS.copy()

        self.out = ''

    def get_cmd(self):
        return utils.get_cmd(self.startup_command, self.replacements)

    def start_server(self):
        self.process = subprocess.Popen(self.get_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.directory)
        self.console = GameConsole()
        self.thread = Thread(target=self.read_output, daemon=True)
        self.thread.start()

    def send_console_command(self, command):
        # TODO server states, like starting, stopped, running, etc.
        if self.process is None:
            print("process is None, ignoring")
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
