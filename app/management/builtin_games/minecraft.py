from app.management.server import GameServer

class MinecraftServer(GameServer):

    DEFAULT_STARTUP_CMD = "java -Xmx{MAX_RAM}M -jar {JARFILE} nogui"
    DEFAULT_STOP_CMD = "stop"
    DEFAULT_START_INDICATOR = "For help, type"
    REPLACEMENTS = {
        "JARFILE": "server.jar",
        "MAX_RAM": "2048"
    }

    # TODO have figure out init args, just kinda setting them all to None by default
    def __init__(self, startup_command = None, stop_command = None, start_indicator = None, dir = None):
        super().__init__("minecraft", startup_command, stop_command, start_indicator, dir)
