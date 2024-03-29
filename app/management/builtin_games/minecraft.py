from app.management.server import GameServer

class MinecraftServer(GameServer):

    DEFAULT_STARTUP_CMD = "java -Xmx{MAX_RAM}M -jar {SERVER_JAR} nogui"
    DEFAULT_STOP_CMD = "stop"
    DEFAULT_START_INDICATOR = "For help, type"
    REPLACEMENTS = {
        "SERVER_JAR": "server.jar",
        "MAX_RAM": "2048"
    }

    SHARED_FILES = ["servarjars"]

    def init(self, server_jar, max_ram, **kwargs):
        self.server_jar = server_jar
        self.max_ram = max_ram
        
    def setup(self):
        self.add_shared_file(self.server_jar, "serverjars")
        self.add_shared_file("libraries", "serverjars")
        
