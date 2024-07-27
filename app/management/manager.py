import os
import yaml
import importlib.util
from pathlib import Path

from app.management.metadata import MetadataFlags
from app.management.storage import Directory, File, StorageManager
from app.management.server import GameServer, GameServerStatus

class ServerManager:
    CLASSES = []

    @staticmethod
    def import_classes_from_directory(directory: Directory, recursion_depth = 0):
        """
        Imports all classes that subclass `GameServer` from all files in directory

        :param directory: The directory to search
        :param recursion_depth: The depth of directories to search. -1 for infinite recursion depth
        :return: The imported classes
        """
        classes: list[type[GameServer]] = []
        for file in directory.list_files():
            if isinstance(file, Directory):
                if recursion_depth != 0:
                    classes += ServerManager.import_classes_from_directory(file, recursion_depth - 1)
                continue
            classes += ServerManager.import_classes_from_file(file)
        return classes
    
    @staticmethod
    def import_classes_from_file(file: File):
        """
        Trys to import `file`, then searchs for classes that extend `GameServer`

        :param file: The file to search
        :return: All classes that extend `GameServer`
        """
        classes: list[type[GameServer]] = []
        spec = importlib.util.spec_from_file_location(Path(file.path).stem, file.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in dir(module):
            if name.startswith("__"):
                continue
            obj = getattr(module, name)
            if obj is GameServer:
                continue
            if type(obj) != type:
                continue
            if not issubclass(obj, GameServer):
                continue
            classes.append(obj)
        return classes
    
    @classmethod
    def load_builtin_games(cls):
        # TODO this works but idk if this is the best way to do this or what a better way would be...
        cls.CLASSES = cls.import_classes_from_directory(Directory(os.path.dirname(__file__)).get_directory("builtin_games"))

    @classmethod
    def get_class(cls, class_name):
        for class_ in cls.CLASSES:
            if class_.__name__ == class_name:
                return class_
        return None
        
    def __init__(self, dir='.', storage_manager = None, ):
        self.dir = dir
        if storage_manager is None:
            storage_manager = StorageManager(self.dir)
        self.storage_manager = storage_manager

        self.servers_yaml = self.storage_manager.servers_dir.get_file("servers.yml")
        self.settings_yaml = self.storage_manager.base_dir.get_file("settings.yml")

        self.servers: list[GameServer] = []

        self.class_map: dict[str, type[GameServer]] = {}

    def register_class(self, game, class_, force = False):
        if not force and game in self.class_map:
            # TODO choose better exceptions. do i need to make my own or is there a better builtin one?
            raise KeyError(f"Game {game} is already registered!")
        self.class_map[game] = class_

    def create_server(self, game, id, **kwargs):
        """
        Creates a new server and does first time initalization.

        To just create a server object for an existing server, use `create_server_obj()`.

        Params are the same as the `GameServer` class.
        :raises KeyError: If a server with the same id and type already exists.
        :return: The created server.
        """
        if self.get_server(game, id) is not None:
            raise KeyError(f"Server {id} of type {game} already exists!")
        server = self.create_server_obj(game, id, **kwargs)
        server.setup()
        return server

    def create_server_obj(self, game: str, id, **kwargs):
        """
        Creates the object for the server by looking up the appropriate class for the type

        NOTE: This just creates the object, to create a new server use `create_server()`.

        Params are the same as the `GameServer` class.
        :return: The created server object.
        """
        parts = game.split('/')
        for i in range(len(parts), 0, -1):
            current_search = '/'.join(parts[:i])
            if current_search in self.class_map:
                found_class = self.class_map[current_search]
                break
        else:
            found_class = GameServer
        server = found_class(id, game, self.storage_manager, **kwargs)
        self.servers.append(server)
        return server

    def auto_start_servers(self):
        for server in self.servers:
            if server.auto_start:
                server.start_server()

    def wait_for_shutdown(self):
        # iterate once to send shutdown signals, than iterate again to actually wait.
        # this way we don't end up waiting for a server to shutdown before starting the shutdown on the next one
        for server in self.servers:
            if server.status not in (GameServerStatus.STOPPED, GameServerStatus.STOPPING):
                server.stop_server()
        for server in self.servers:
            if server.process is not None:
                server.process.wait()
    
    def get_server(self, game, id):
        for server in self.servers:
            if server.game == game and server.id == id:
                return server
        return None # technically None could be returned implicitly but i added this for readablity

    def load_settings(self):
        if self.settings_yaml.exists():
            self.reload_settings()
        else:
            for cls in self.CLASSES:
                if cls.default_type is not None:
                    self.register_class(cls.default_type, cls, False)

    def reload_settings(self):
        self.class_map.clear()
        with self.settings_yaml.open() as file:
            try:
                settings = yaml.safe_load(file)
            except yaml.YAMLError as error:
                print("Error reading settings.yml:", error)

        for game, class_ in settings['class_map'].items():
            self.register_class(game, self.get_class(class_), True)

    def save_settings(self):
        self.settings_yaml.ensure_parent_exists()
        with self.settings_yaml.open("w") as file:
            yaml.safe_dump({"class_map": {k: v.__name__ for k, v in self.class_map.items()}}, file)

    def load_servers(self):
        if self.servers_yaml.exists():
            self.reload_servers()
        else:
            pass # no extra setup is required if there is no file

    def reload_servers(self):
        self.servers.clear()
        with self.servers_yaml.open() as file:
            try:
                servers = yaml.safe_load(file) or []
            except yaml.YAMLError as error:
                print("Error reading servers.yml:", error)
        for server in servers:
            self.create_server_obj(**server)

    def save_servers(self):
        self.servers_yaml.ensure_parent_exists()
        with self.servers_yaml.open("w") as file:
            yaml.safe_dump([s.as_dict(flat=True, filter=MetadataFlags.SETTINGS) for s in self.servers], file, sort_keys=False)
        