from typing import Annotated
from app.management.metadata import MetadataFlags, Setting, ValueMetadata
from app.management.server import GameServer

class MinecraftServer(GameServer):

    default_type = 'minecraft'

    startup_command = "java -Xmx{MAX_RAM}M -jar {SERVER_JAR} nogui"
    stop_command    = "stop"
    start_indicator = "For help, type"

    server_jar: Annotated[str, ValueMetadata(MetadataFlags.SETTINGS | MetadataFlags.WRITABLE | MetadataFlags.REPLACEMENT)] = "server.jar"
    max_ram: Annotated[int, ValueMetadata(MetadataFlags.SETTINGS | MetadataFlags.WRITABLE | MetadataFlags.REPLACEMENT)] = 2048

    BINS = ["servarjars"]
        
    def setup(self):
        self.add_shared_file(self.server_jar, "serverjars")
        self.add_shared_file("libraries", "serverjars")
        
