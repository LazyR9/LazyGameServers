import os
import yaml
import importlib.util
from pathlib import Path

from app.management.storage import StorageManager
from app.management.server import GameServer

class ServerManager:
    CLASSES = []

    @staticmethod
    def load_classes(directory: str):
        """
        Loads all the classes it can find in dir

        :param dir: The direction to search
        :return: The found classes
        """
        classes: list[type[GameServer]] = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path):
                continue
            spec = importlib.util.spec_from_file_location(Path(directory).stem, file_path)
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
        
    def __init__(self, dir='.', storage_manager = None, ):
        self.dir = dir
        if storage_manager is None:
            storage_manager = StorageManager(self.dir)
        self.storage_manager = storage_manager

        self.servers_yaml = os.path.join(self.storage_manager.servers_dir, "servers.yml")
        self.settings_yaml = os.path.join(self.dir, "settings.yml")

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
        with open(self.settings_yaml) as file:
            try:
                settings = yaml.safe_load(file)
            except yaml.YAMLError as error:
                print("Error reading settings.yml:", error)

    def save_settings(self):
        with open(self.settings_yaml, "w") as file:
            yaml.safe_dump({"class_map": {k: v.__name__ for k, v in self.class_map.items()}}, file)

    def load_servers(self):
        with open(self.servers_yaml) as file:
            try:
                servers = yaml.safe_load(file)
            except yaml.YAMLError as error:
                print("Error reading servers.yml:", error)
        print(servers)
        for server in servers:
            self.create_server_obj(**server)

    def save_servers(self):
        with open(self.servers_yaml, "w") as file:
            yaml.safe_dump([s.as_dict() for s in self.servers], file, sort_keys=False)
        