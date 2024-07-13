import os
import yaml
import importlib.util
from pathlib import Path

from app.management.storage import Directory, StorageManager
from app.management.server import GameServer

class ServerManager:
    CLASSES = []

    @staticmethod
    def load_classes(directory: Directory):
        """
        Loads all the classes it can find in dir

        :param dir: The direction to search
        :return: The found classes
        """
        classes: list[type[GameServer]] = []
        for file in directory.list_files():
            if issubclass(type(file), Directory):
                continue
            spec = importlib.util.spec_from_file_location(Path(directory.path).stem, file.path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name in dir(module):
                if name.startswith("__"):
                    continue
                obj = getattr(module, name)
                if obj == GameServer:
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
        cls.CLASSES = cls.load_classes(Directory(os.path.dirname(__file__)).get_directory("builtin_games"))

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

    def create_server(self, game, id, startup_cmd = None, stop_cmd = None, start_indicator = None, **kwargs):
        """
        Creates a new server and does first time initalization.

        To just create a server object for an existing server, use `create_server_obj()`.

        Params are the same as the `GameServer` class.
        :raises KeyError: If a server with the same id and type already exists.
        :return: The created server.
        """
        if self.get_server(game, id) is not None:
            raise KeyError(f"Server {id} of type {game} already exists!")
        server = self.create_server_obj(game, id, startup_cmd, stop_cmd, start_indicator, **kwargs)
        server.setup()
        return server

    def create_server_obj(self, game: str, id, startup_cmd = None, stop_cmd = None, start_indicator = None, **kwargs):
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
        server = found_class(id, game, self.storage_manager, startup_cmd, stop_cmd, start_indicator, **kwargs)
        self.servers.append(server)
        return server
    
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
            yaml.safe_dump([s.as_dict() for s in self.servers], file, sort_keys=False)
        