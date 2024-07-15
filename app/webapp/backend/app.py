from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.management.manager import ServerManager

from .routers import servers

# i have to inject this code because starlette treats %2F as a normal slash.
# the injection method is a copy of _utils.get_route_path,
# except it uses the decoded raw_path instead of just the path,
# which is already url decoded
# TODO see if there is another way to do this
import re
from starlette import _utils
from starlette.types import Scope
def injection(scope: Scope) -> str:
    root_path = scope.get("root_path", "")
    route_path = re.sub(r"^" + root_path, "", scope["raw_path"].decode())
    return route_path
_utils.get_route_path.__code__ = injection.__code__

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager: ServerManager = app.state.server_manager
    manager.load_settings()
    manager.load_servers()
    manager.auto_start_servers()
    yield
    manager.wait_for_shutdown()
    manager.save_settings()
    manager.save_servers()

app = FastAPI(root_path="/api", lifespan=lifespan)

app.include_router(servers.router)
