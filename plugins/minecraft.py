import json
from typing import Annotated, Any
import urllib
import urllib.request

from app.management.wizard import *
from app.management.metadata import MetadataFlags, ValueMetadata
from app.management.server import GameServer

class MinecraftServer(GameServer):

    default_type = 'minecraft'

    startup_command = "java -Xmx{max_ram}M -jar {server_jar} nogui"
    stop_command    = "stop"
    start_indicator = "For help, type"

    server_jar: Annotated[str, ValueMetadata(MetadataFlags.SETTINGS | MetadataFlags.WRITABLE | MetadataFlags.REPLACEMENT)] = "server.jar"
    max_ram: Annotated[int, ValueMetadata(MetadataFlags.SETTINGS | MetadataFlags.WRITABLE | MetadataFlags.REPLACEMENT)] = 2048

    BINS = ["servarjars"]

    VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    
    _version_manifest: dict[str, Any] | None = None
    _version_data: dict[str, dict[str, Any]] = {}
    
    @classmethod
    def get_version_from_manifest(cls, version):
        for version_data in cls.get_version_manifest()["versions"]:
            if version_data["id"] == version:
                return version_data
        return None
    
    @classmethod
    def get_version_manifest(cls):
        if cls._version_manifest is None:
            with urllib.request.urlopen(cls.VERSION_MANIFEST_URL) as response:
                cls._version_manifest = json.load(response)
        assert cls._version_manifest is not None
        return cls._version_manifest
    
    @classmethod
    def get_version_data(cls, version: str):
        if version not in cls._version_data:
            version_metadata = cls.get_version_from_manifest(version)
            if version_metadata is None:
                return None
            with urllib.request.urlopen(version_metadata["url"]) as response:
                cls._version_data[version] = json.load(response)
        return cls._version_data[version]
    
    async def setup(self, wizard: Wizard):
        await wizard.input("Please accept the Minecraft EULA: https://aka.ms/MinecraftEULA", BoolInput(), [force_eula])
        with self.get_file("eula.txt").open("w") as file:
            file.write("eula=true")
        cls = self.__class__
        
        version = await wizard.input("Select a version", StringInput(), [SingleChoiceValidator([v["id"] for v in cls.get_version_manifest()["versions"]])])
        filename = f"vanilla-{version}.jar"
        file = self.storage_manager.get_bin(self.default_type, "serverjars").get_file(filename)
        if not file.exists():
            file.ensure_parent_exists()
            version_data = cls.get_version_data(version)
            assert version_data is not None
            urllib.request.urlretrieve(version_data["downloads"]["server"]["url"], file.path)
        ram = await wizard.input("How much ram? (MB)", IntInput(), [RangeValidator(512, 16384), StepValidator(256)])
        self.max_ram = ram

        libraries = self.storage_manager.get_bin(self.default_type, "serverjars").get_directory("libraries")
        libraries.ensure_exists()
        self.add_shared_file(filename, "serverjars", dest_name=self.server_jar)
        self.add_shared_file("libraries", "serverjars")

def force_eula(input):
    if not input:
        raise ValidationError("You need to accept the EULA!")
