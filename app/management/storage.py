from enum import Enum, auto
import os
import shutil
from typing import Any, overload, Literal

from app import utils

class FileType(Enum):
    NONE = 0
    FILE = auto()
    DIRECTORY = auto()

class File:
    type = FileType.FILE

    def __init__(self, path, parent: 'Directory | None' = None):
        self.path = utils.correct_file_seperator(path)
        self.name = os.path.basename(self.path)
        self._parent = parent

    @overload
    def get_contents(self, binary: Literal[False] = ...) -> str: ...

    @overload
    def get_contents(self, binary: Literal[True]) -> bytes: ...

    def get_contents(self, binary = False):
        assert self.__class__ == File
        mode = 'rb' if binary else 'rt'
        with self.open(mode) as file:
            return file.read()
        
    def exists(self):
        return os.path.exists(self.path)
        
    def open(self, mode="rt"):
        return open(self.path, mode)
    
    def delete(self):
        return os.remove(self.path)
    
    def get_parent(self):
        if self._parent is None:
            self._parent = Directory(os.path.dirname(self.path))
        return self._parent
    
    def ensure_parent_exists(self):
        self.get_parent().ensure_exists()
    
    def as_dict(self, include_contents = False):
        value: dict[str, Any] = {"name": self.name, "type": self.type.name}
        if include_contents:
            contents = self.get_contents()
            if contents is not None:
                value["contents"] = contents
        return value
    
    def __repr__(self):
        return f"<{self.__class__.__name__} path=\"{self.path}\">"

class Directory(File):
    type = FileType.DIRECTORY

    def get_contents(self, binary = False):
        raise IsADirectoryError("Cannot get contents of directory! (Did you mean list_files() instead?)")

    def list_files(self) -> list[File]:
        # We ignore return type here because get_file_or_dir() returns None on non-existant path,
        # but since the argument comes from os.listdir(), the path is guaranteed to exist
        # (ignoring race conditions because I don't want to think about that)
        return [self.get_file_or_dir(file) for file in os.listdir(self.path)] # pyright: ignore[reportReturnType]
    
    def get_file(self, filename: str):
        path = self._get_file_path(filename)
        return File(path, self)
        
    def get_directory(self, dirname: str):
        path = self._get_file_path(dirname)
        return Directory(path, self)
    
    def get_file_or_dir(self, filename) -> 'File | Directory | None':
        if filename in ('', '.'):
            return self
        path = self._get_file_path(filename)
        if not os.path.exists(path):
            return None
        if os.path.isfile(path):
            return File(path, self)
        else:
            return Directory(path, self)
    
    def delete(self):
        return shutil.rmtree(self.path)
        
    def ensure_exists(self):
        os.makedirs(self.path, exist_ok=True)
        
    def as_dict(self, include_contents = False):
        return self.dir_as_dict(include_contents)
        
    def dir_as_dict(self, recursion_depth = 0):
        """
        Gets a dictionary representing this directory, with 

        :param include_contents: The depth subdirectories list out their files, defaults to 0 meaning to not include files.
        :return: A dictionary representation of this directory
        """
        value = super().as_dict(False)
        if recursion_depth:
            value.update({
                "files": [file.dir_as_dict(recursion_depth - 1) if isinstance(file, Directory) else file.as_dict(False) for file in self.list_files()]
            })
        return value

    def _get_file_path(self, filename: str):
        return os.path.join(self.path, filename)

# TODO rewrite some storage manager code to use file objects instead of path strings
class StorageManager:
    def __init__(self, base_dir = '.'):
        self.base_dir = Directory(base_dir)
        self.servers_dir = self.base_dir.get_directory("servers")
        self.storage_dir = self.base_dir.get_directory("storage")

    def get_bin(self, game, bin):
        return self.storage_dir.get_directory(game).get_directory(bin)

    def get_shared_file(self, game, bin, file):
        return self.get_bin(game, bin).get_file_or_dir(file)

    def get_server_folder(self, server: 'GameServer'):
        # FUTURE use UUIDs for server directories instead of type and name
        return self.servers_dir.get_directory(server.game).get_directory(server.id)
    
    def get_file_from_server(self, server: 'GameServer', file: str):
        return self.get_server_folder(server).get_file(file)
    
    def create_server_folder(self, server: 'GameServer'):
        folder = self.get_server_folder(server).path
        if os.path.exists(folder):
            raise FileExistsError(f"Unable to create server: {folder} already exists")
        os.makedirs(folder)
        utils.chown_file(folder, server.config.subprocess_user)

    # TODO have a class for symlinks to make these two functions easier
    def add_shared_file_to_server(self, game: str, bin: str, file: str, server: 'GameServer', dest_name: str | None = None): # seperate game for file and server, helpful because sub games are a thing
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
        if src_file is None:
            raise FileNotFoundError(f"Source file {file} doesn't exist!")
        if dest_name is None:
            dest_name = os.path.basename(src_file.path)
        dest_file = os.path.join(self.get_server_folder(server).path, dest_name)
        if os.path.exists(dest_file):
            raise FileExistsError(f"File {dest_file} already exists!")
        os.symlink(os.path.abspath(src_file.path), dest_file)

    def remove_shared_file_from_server(self, server: 'GameServer', file):
        file = self.get_file_from_server(server, file)
        if file.exists():
            raise FileNotFoundError(f"File {file} doesn't exist!")
        # TODO is this the best exception here?
        if not os.path.islink(file.path):
            raise FileExistsError(f"File {file} is not a symlink!")
        # TODO better check to make sure its in central storage,
        # but also not likely there will be other symlinks in a server folder
        if self.storage_dir.path not in os.readlink(file.path):
            raise FileExistsError(f"File {file} does not point to central storage!")
        os.unlink(file.path)

# circular imports yaaaaay (it's just here so type hints work)
from app.management.server import GameServer
