import os

from app import utils

class StorageManager:
    def __init__(self, base_dir = '.'):
        self.base_dir = base_dir
        self.servers_dir = os.path.join(self.base_dir, "servers")
        self.storage_dir = os.path.join(self.base_dir, "storage")

    def get_bin(self, game, bin):
        return os.path.join(self.storage_dir, utils.correct_file_seperator(game))

    def get_shared_file(self, game, bin, file):
        return os.path.join(self.get_bin(game, bin), file)

    def get_server_folder(self, server: 'GameServer'):
        return os.path.join(self.servers_dir, utils.correct_file_seperator(server.game), server.id)
    
    def get_file_from_server(self, server, file):
        return os.path.join(self.get_server_folder(server), file)
    
    def create_server_folder(self, server: 'GameServer'):
        folder = self.get_server_folder(server)
        if os.path.exists(folder):
            raise FileExistsError(f"Unable to create server: {folder} already exists")
        os.makedirs(folder)

    def add_shared_file_to_server(self, game: str, bin: str, file: str, server: 'GameServer', dest_name: str = None): # seperate game for file and server, helpful because sub games are a thing
        """
        Add a file from shared storage to a server

        :param game: The game to get the file from
        :param bin: The game's bin to search
        :param file: The file to add
        :param server: The server to add the file to
        :param dest_name: The name of the file in the server, defaults to None meaning to use the same name as the source file
        :raises FileExistsError: If a file exists in the destination
        """
        src_file = self.get_shared_file(game, bin, file)
        if dest_name is None:
            dest_name = os.path.basename(src_file)
        dest_file = os.path.join(self.get_server_folder(server), dest_name)
        if os.path.exists(dest_file):
            raise FileExistsError(f"File {dest_file} already exists!")
        os.symlink(os.path.abspath(src_file), dest_file)

    def remove_shared_file_from_server(self, server: 'GameServer', file):
        file_path = self.get_file_from_server(server, file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file} doesn't exist!")
        # TODO is this the best exception here?
        if not os.path.islink(file_path):
            raise FileExistsError(f"File {file} is not a symlink!")
        # TODO better check to make sure its in central storage,
        # but also not likely there will be other symlinks in a server folder
        if self.storage_dir not in os.readlink(file_path):
            raise FileExistsError(f"File {file} does not point to central storage!")
        os.unlink(file_path)

# circular imports yaaaaay (it's just here so type hints work)
from app.management.server import GameServer
