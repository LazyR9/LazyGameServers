from app.management.manager import ServerManager

ServerManager.load_builtin_games()
manager = ServerManager()
manager.load_settings()
manager.load_servers()

# TODO finish writing main.py once everything is in a workable state lol
print(manager.servers)

# TODO replace use propper logging instead of print statements
