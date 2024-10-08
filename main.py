import argparse
import os
from dotenv import load_dotenv
import uvicorn

from app.management.manager import ServerManager
from app.webapp.backend.app import app


parser = argparse.ArgumentParser()

def add_arg(arg: str, default, **kwargs):
    parser.add_argument(f'--{arg}', default=os.environ.get(arg.upper(), default), **kwargs)

add_arg("directory", ".")
add_arg("address", "localhost")
add_arg("port", 8000, type=int)
add_arg("debug", False, action="store_true")


args = parser.parse_args()
load_dotenv()

ServerManager.load_builtin_plugins()

server_manager = ServerManager(args.directory)
# TODO move this to the lifespan function on the backend once plugins can reload
server_manager.load_plugins()

# TODO finish writing main.py once everything is in a workable state lol

# TODO use propper logging instead of print statements
print("Starting server...")
# TODO is this how to server manager should be attached?
# (maybe a factory in app.py??)
app.state.server_manager = server_manager
# FUTURE support multiple workers, especially if i add multiple users with their own servers
if __name__ == "__main__":
    uvicorn.run("main:app", host=args.address, port=args.port, reload=args.debug)
