import subprocess
import psutil
from threading import Thread
from typing import Callable
from enum import Enum, auto
import datetime

from app import utils
from app.management.storage import StorageManager

# TODO this can support anything that is run through the command line,
# should i be naming everything with "Game"? 

# TODO would states be a better name than status?
class GameServerStatus(Enum):
    STOPPED = 0
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()

class GameConsoleLine:
    def __init__(self, line: str, error: bool = False, timestamp: datetime.datetime = None):
        self.timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)
        self.line = line
        self.error = error

    def as_dict(self):
        return {
            "line": self.line,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }

class GameConsole:
    def __init__(self):
        self.lines: list[GameConsoleLine] = []
        self.listeners: list[Callable[[GameConsoleLine]]] = []

    def add_line_listener(self, listener):
        """
        Adds `listener` to a list of functions to be called when a new line of output is added.
        The only parameter passed is the string that was added.
        """
        self.listeners.append(listener)

    def add_line(self, line, error = False):
        console_line = GameConsoleLine(line, error)
        self.lines.append(console_line)
        # Make a copy so changing the original list doesn't break the loop
        for listener in self.listeners[:]:
            listener(console_line)

    def as_dict(self):
        return {
            "lines": [line.as_dict() for line in self.lines],
        }
    
    def clear(self):
        self.lines.clear()
        # TODO listener for when console is cleared?

    def get_str(self):
        """
        Concatenates all lines of output into one string.
        """
        return ''.join([line.line for line in self.lines])

    def print(self):
        print(self.get_str())

# TODO more consistent usage of command vs cmd
class GameServer:

    # these are defaults for the class, the lowercase versions are instance specific
    # TODO python copies these class attributes to each instance,
    # so that each instance's value can differ from the class.
    # For example,
    #####
    # >>> class MyClass:
    # >>>   SOME_VALUE = 'default'
    # >>> x = MyClass()
    # >>> x.SOME_VALUE = 'something else'
    # >>> MyClass.SOME_VALUE != x.SOME_VALUE
    # True
    #####
    # so would just using a class default as the attribute work?
    # should it be capital?

    # command line command to start server
    DEFAULT_STARTUP_CMD = None
    # command to send to console to shutdown server, "^C" means to send a SIGTERM
    DEFAULT_STOP_CMD = "^C"
    # text to look for in the console to know when the server is finished loading
    # if the start_indicator is None, this server doesn't have a way to know when it is done starting.
    # this can also be an empty string to indicate that the status will be set manually, like through a plugin or mod.
    DEFAULT_START_INDICATOR = None

    # default values for extra data can be specified here
    CUSTOM_DATA: dict[str, str] = {}
    REPLACEMENTS: list[str] = []

    # name of folders that hold other files and folders to be shared across server instances
    BINS = []

    def __init__(self, id, game, storage_manager: StorageManager, startup_command: str = None, stop_command: str = None, start_indicator: str = None, **kwargs):
        """
        Creates a new server object.
        
        THIS SHOULD NOT BE CALLED OR OVERRIDDEN!
        A `ServerManager` instance should be used to get existing servers or create new ones.
        The `init()` function should be used if extra processing should be done when the object is created,
        as it only takes extra data and won't need to be updated, unlike this function whose parameters might change.

        :param id: The ID to use for this server.
        :param game: The game identifier of this server
        :param storage_manager: The StorageManager this server should use to get files
        :param startup_command: The command to use to start the server, defaults to the class attribute of the same name
        :param stop_command: The input to send to the stdin of the process, defaults to the class attribute of the same name
        :param start_indicator: What text to look for in the output that signals that the server is fully started, defaults to the class attribute of the same name
        """
        self.id = id
        self.game = game
        self.storage_manager = storage_manager

        self.startup_command = startup_command if startup_command is not None else self.DEFAULT_STARTUP_CMD
        self.stop_command = stop_command if stop_command is not None else self.DEFAULT_STOP_CMD
        self.start_indicator = start_indicator if start_indicator is not None else self.DEFAULT_START_INDICATOR

        self.process = None
        self.psutil = None
        self.custom_data = self.CUSTOM_DATA.copy()
        self.status = GameServerStatus.STOPPED
        self.console = GameConsole()

        self.ensure_directory()

        # remember all custom data so it can be accessed later
        self.custom_data.update(kwargs)
        self.init(**kwargs)

    def init(self, **kwargs):
        """
        Do any extra setup on this object. This is called at the end of `__init__()`.
        
        This function serves as an easier way to initalize custom fields,
        as it takes no args and doesn't need to call super() because the base class does nothing.
        `kwargs` is everything in `custom_data`.
        This is useful for having named parameters instead of refering to a value using a string.
        """

    def setup(self):
        """
        Does first time setup on this server.
        Usually should only be called the first time the server is created,
        not when the object is created.

        For example, this could be adding required downloads from shared storage,
        or downloading other files needed to run the server.
        """

    def get_cmd(self):
        """
        Gets the command for this server.

        Anything in curly braces will get replaced by the corresponding value in `replacements`.
        """
        return utils.get_cmd(self.startup_command, self.get_replacements())
    
    def get_replacements(self):
        # create a copy of custom data, as long as the key is in the whitelist.
        # it also allows values that don't appear in the default custom data list,
        # in case extra custom data is specified that needs to be replaced.
        return {k: v for k, v in self.custom_data.items() if k in self.__class__.REPLACEMENTS or k not in self.__class__.CUSTOM_DATA}

    def start_server(self):
        """
        Spawns the server subprocess and run threads to monitor it.
        Returns True if the server started, False if it was already running.
        """
        if self.status != GameServerStatus.STOPPED:
            return False
        self.status = GameServerStatus.STARTING if self.start_indicator is not None else GameServerStatus.RUNNING
        self.process = subprocess.Popen(self.get_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.get_directory())
        self.ps = psutil.Process(self.process.pid)
        self.console.clear()
        if self.start_indicator:
            self.console.add_line_listener(self._find_start_indicator)
        # One thread monitors stdout, and the other monitors stderr
        Thread(target=self._read_output, args=(True, ), daemon=True).start()
        Thread(target=self._read_output, args=(False,), daemon=True).start()
        Thread(target=self._wait_for_stop, daemon=True).start()
        return True

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

    def as_dict(self):
        data = {
            "id": self.id,
            "game": self.game,
            "startup_cmd": self.startup_command,
            "stop_cmd": self.stop_command,
            "start_indicator": self.start_indicator,
            # TODO should the status be under stats?
            "status": self.status.name,
            "stats": self.get_stats(),
        }
        for key, item in self.custom_data.items():
            if key in data:
                # TODO what to do when keys collide? can't happen through loading a config file
                # but could happen if a key is set through a script
                print("custom data trying to override builtin data!")
                continue
            data[key] = item
        return data
    
    def get_stats(self):
        return {
            "cpu": self.ps.cpu_percent() if self.status != GameServerStatus.STOPPED else 0,
            "memory": 2_500_000,
            "players": 4,
            "max_players": 10,
        }
    
    def ensure_directory(self):
        try:
            self.storage_manager.create_server_folder(self)
        except FileExistsError:
            # aparently catching errors is better than checking when it comes to files
            # however, the function being called checks instead of catching exception so...
            pass

    def _read_output(self, error = False):
        """
        Constantly monitors the stdout of the subprocess, and adds it to the server's console object.
        Will block until the program exits, only call on another thread.
        """
        output = self.process.stderr if error else self.process.stdout
        while self.process.poll() is None:
            line = output.readline().decode("utf8")
            if not line: # an empty line means eof, happens when a program writes eof before actually termainating
                break
            self.console.add_line(line, error)
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

    def _find_start_indicator(self, line: GameConsoleLine):
        """
        Looks for the start indicator in `line`.
        Used as console line listener, and doesn't handle special cases like the indicator being `None` or an empty string.
        """
        if self.start_indicator not in line.line:
            return
        self.status = GameServerStatus.RUNNING
        self.console.listeners.remove(self._find_start_indicator)
