from app.management.server import GameServer

class MinecraftServer(GameServer):

    DEFAULT_STARTUP_CMD = "java -Xmx{MAX_RAM}M -jar {SERVER_JAR} nogui"
    DEFAULT_STOP_CMD = "stop"
    DEFAULT_START_INDICATOR = "For help, type"
    CUSTOM_DATA = {
        "server_jar": "server.jar",
        "max_ram": "2048",
    }
    REPLACEMENTS = ["server_jar", "max_ram"]

    BINS = ["servarjars"]

    def init(self, server_jar, max_ram, **kwargs):
        self.server_jar = server_jar
        self.max_ram = max_ram
        
    def setup(self):
        self.add_shared_file(self.server_jar, "serverjars")
        self.add_shared_file("libraries", "serverjars")
        
