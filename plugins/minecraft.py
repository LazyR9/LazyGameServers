import json
from typing import Annotated
import urllib
import urllib.request

from app.management.metadata import MetadataFlags, Setting, ValueMetadata
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
    
    _version_manifest = None
    _version_data = {}
    
    @classmethod
    def get_version_from_manifest(cls, version):
        for version_data in cls._version_manifest["versions"]:
            if version_data["id"] == version:
                return version_data
        return None
    
    # TODO expand the plugin api to have an interactive setup process, something like:
    # 
    # def setup(self):
    #     version = self.ask_user("What version?", choices=self.get_versions())
    #     self.download_version(version)
    #     if not self.ask_user("Agree to license", answer_type = AnswerType.BOOL):
    #         self.show_error("You need to agree to the license!")
    #         self.cancel()
    def setup(self):
        cls = self.__class__
        if cls._version_manifest is None:
            with urllib.request.urlopen(cls.VERSION_MANIFEST_URL) as response:
                cls._version_manifest = json.load(response)
        latest_version = cls._version_manifest["latest"]["release"]
        self.server_jar = f"vanilla-{latest_version}.jar"
        file = self.storage_manager.get_bin(self.default_type, "serverjars").get_file(self.server_jar)
        if not file.exists():
            if latest_version not in cls._version_data:
                with urllib.request.urlopen(cls.get_version_from_manifest(latest_version)["url"]) as response:
                    cls._version_data[latest_version] = json.load(response)
            urllib.request.urlretrieve(cls._version_data[latest_version]["downloads"]["server"]["url"], file.path)

        self.add_shared_file(self.server_jar, "serverjars")
        self.add_shared_file("libraries", "serverjars")
        
