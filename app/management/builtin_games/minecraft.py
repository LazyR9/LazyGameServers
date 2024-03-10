from app.management.server import GameServer

class MinecraftServer(GameServer):

    DEFAULT_STARTUP_CMD = "java -Xmx{MAX_RAM}M -jar {JARFILE} nogui"
    DEFAULT_STOP_CMD = "stop"
    REPLACEMENTS = {
        "JARFILE": "server.jar",
        "MAX_RAM": "2048"
    }

    def __init__(self, startup_command = None, stop_command = None, dir = None):
        super().__init__("minecraft", startup_command, stop_command, dir)
