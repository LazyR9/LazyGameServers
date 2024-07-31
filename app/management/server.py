import subprocess
import psutil
from threading import Thread
from typing import Annotated
from enum import Enum, auto
import datetime

from app import utils
from app.management.events import ConsoleClearEvent, ConsoleLineEvent, GameServerEvent, GameServerEventListener, GameServerEventType, StatusEvent
from app.management.metadata import MetadataFlags, Setting, ValueMetadata
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
    def __init__(self, server: 'GameServer'):
        self.lines: list[GameConsoleLine] = []
        self.server = server

    def add_line(self, line, error = False):
        console_line = GameConsoleLine(line, error)
        self.lines.append(console_line)
        self.server.emit_event(ConsoleLineEvent(console_line))

    def as_dict(self):
        return {
            "lines": [line.as_dict() for line in self.lines],
        }
    
    def clear(self):
        self.lines.clear()
        self.server.emit_event(ConsoleClearEvent())

    def get_str(self):
        """
        Concatenates all lines of output into one string.
        """
        return ''.join([line.line for line in self.lines])

    def print(self):
        print(self.get_str())

# TODO by directly subclassing GameServer, extra server types can completely override all behaviour
# maybe change to use a class only used for storing data and providing extra callbacks, without overriding anything from this class
class GameServer:
    default_type: str = None

    id: Setting[str] = None
    game: Setting[str] = None
    status: Annotated[GameServerStatus, ValueMetadata(MetadataFlags.NONE, lambda status: status.name)]

    # class defaults, can be overridden on subclasses and also differ on the actual objects

    # command line command to start server
    startup_command: Setting[str] = None
    # command to send to console to stop server, "^C" means to send a SIGTERM
    stop_command: Setting[str] = "^C"
    # text to look for in the console to know when the server is finished loading
    # if the start_indicator is None, this server doesn't have a way to know when it is done starting.
    # this can also be an empty string to indicate that the status will be set manually, like through a plugin or mod.
    start_indicator: Setting[str] = None

    # whether or not this server should start as soon as soon as it is loaded
    auto_start: Setting[bool] = False
    # whether or not the server should attempt to automatically restart if it detects a crash
    restart_on_crash: Setting[bool] = True
    # amount of time in seconds that a process has to stop,
    # after this we will forcably kill it
    stop_timeout: Setting[float] = 30

    # name of folders that hold other files and folders to be shared across server instances
    BINS = []

    def __init__(self, storage_manager: StorageManager, **kwargs):
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
        self.storage_manager = storage_manager

        self.process = None
        self.psutil = None
        self.status = GameServerStatus.STOPPED
        self.console = GameConsole(self)

        self._listeners: list[GameServerEventListener] = []

        extra_data = {}
        for key, value in kwargs.items():
            # only set attributes which already exist
            # TODO disallow some attributes to be set, like methods or builtin python attributes
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                extra_data[key] = value

        self.ensure_directory()

        self.init(**extra_data)

    def init(self, **extra_data):
        """
        Do any extra setup on this object. This is called at the end of `__init__()`.
        This is called everytime the server is loaded from disk.

        For a function that is called only once when a server is created, use `setup()`.
        
        This function should be used instead of overriding `__init__()`
        because it may get called again without recreating the object,
        for example if the server is reloaded from disk.

        `kwargs` is any extra data that was found in the config that didn't match any fields defined in the class.
        """

    def setup(self):
        """
        Does first time setup on this server.
        Usually should only be called the first time the server is created,
        not when the object is created.

        For example, this could be adding required downloads from shared storage,
        or downloading other files needed to run the server.
        """

    def get_command(self):
        """
        Gets the command for this server.

        Anything in curly braces will get replaced by the corresponding value in `replacements`.
        """
        return utils.get_command(self.startup_command, self.get_replacements())
    
    def get_replacements(self):
        return {k: v for k, v, *_ in ValueMetadata.iter_metadatas(self, filter=lambda meta: meta.flags & MetadataFlags.REPLACEMENT)}

    def start_server(self):
        """
        Spawns the server subprocess and run threads to monitor it.
        Returns True if the server started, False if it was already running.
        """
        if self.status != GameServerStatus.STOPPED:
            return False
        self.status = GameServerStatus.STARTING if self.start_indicator is not None else GameServerStatus.RUNNING
        self.process = subprocess.Popen(self.get_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.get_directory().path)
        self.ps = psutil.Process(self.process.pid)
        self.console.clear()
        if self.start_indicator:
            self.add_event_listener(self._find_start_indicator, GameServerEventType.CONSOLE_LINE)
        # One thread monitors stdout, and the other monitors stderr
        Thread(target=self._read_output, args=(True, ), daemon=True).start()
        Thread(target=self._read_output, args=(False,), daemon=True).start()
        Thread(target=self._wait_for_stop, daemon=True).start()
        self.emit_status_event()
        return True

    def stop_server(self):
        self.status = GameServerStatus.STOPPING
        if self.stop_command == "^C":
            utils.send_ctrl_c(self.process)
        else:
            self.send_console_command(self.stop_command)
        Thread(target=self._kill_after_timeout, daemon=True).start()
        self.emit_status_event()

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

    # TODO this function is kinda a mess, clean up somehow?
    def as_dict(self, include_metadata = False, flat = False, filter: MetadataFlags = None):
        def empty_dict():
            return ValueMetadata(MetadataFlags.SETTINGS).as_dict({}) if include_metadata else {}
        
        def get(dict):
            return dict["value"] if include_metadata else dict


        # TODO should the status be under stats?
        data = {"server_data": empty_dict()} if not flat else {}
        
        # TODO this is kinda a scuffed way to do this
        for name, value, metadata, cls in ValueMetadata.iter_metadatas(self):
            if filter is not None and not filter & metadata.flags:
                continue

            if flat or cls is GameServer:
                d = data
            else:
                d = get(data["server_data"])
                if cls.__name__ not in d:
                    d[cls.__name__] = empty_dict()
                d = get(d[cls.__name__])

            d[metadata.name or name] = metadata.as_dict(value, transform=False) if include_metadata else value
        
        if not flat:
            # Remove and reinsert server_data so it's at the end of the dict
            server_data = data.pop("server_data")
            data["server_data"] = server_data
        return data
    
    def update_from_dict(self, data: dict):
        failed_keys = []

        for name, value, metadata, cls in ValueMetadata.iter_metadatas(self):
            if name not in data:
                continue
            if not metadata.flags & MetadataFlags.WRITABLE:
                failed_keys.append(name)
                continue
            setattr(self, name, data[name])
        
        return failed_keys
    
    def get_stats(self) -> Annotated[dict, ValueMetadata(MetadataFlags.NONE)]:
        # TODO should extra stats provided by a server be under a specific key?
        if self.status == GameServerStatus.STOPPED:
            return {
                "cpu": 0,
                "memory": 0,
            }
        with self.ps.oneshot():
            return {
                "cpu": self.ps.cpu_percent(),
                "memory": self.ps.memory_info().rss,
            }
    
    def ensure_directory(self):
        try:
            self.storage_manager.create_server_folder(self)
        except FileExistsError:
            # aparently catching errors is better than checking when it comes to files
            # however, the function being called checks instead of catching exception so...
            pass

    def add_event_listener(self, func, filter = None):
        listener = GameServerEventListener(func, filter)
        self._listeners.append(listener)
        return listener

    def emit_event(self, event: GameServerEvent):
        """
        Passes the event to `call()` on all listeners,
        which will then decide if the filter on the listener matches
        and then call the underlying function.

        :param event: The event to emit.
        """
        # remove deregistered listeners from list
        self._listeners = [listener for listener in self._listeners if listener._registered]
        for listener in self._listeners:
            event.listener = listener
            # the events are filtered in the call method, so this loops over all listeners
            listener.call(event)

    def emit_status_event(self):
        """Convenience function that emits an event with the current status of the server"""
        self.emit_event(StatusEvent(self.status))

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
        crash = self.status != GameServerStatus.STOPPING
        self.status = GameServerStatus.STOPPED
        self.emit_status_event()
        if crash:
            print(f"Server {self.game}/{self.id} crashed!")
            if self.restart_on_crash:
                print("Auto restarting...")
                self.start_server()

    def _find_start_indicator(self, event: ConsoleLineEvent):
        """
        Looks for the start indicator in `line`.
        Used as console line listener, and doesn't handle special cases like the indicator being `None` or an empty string.
        """
        if self.start_indicator not in event.line.line:
            return
        self.status = GameServerStatus.RUNNING
        self.emit_status_event()
        event.listener.deregister()

    def _kill_after_timeout(self):
        try:
            self.process.wait(self.stop_timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
