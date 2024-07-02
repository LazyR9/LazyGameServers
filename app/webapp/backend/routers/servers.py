from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.management.manager import ServerManager
from app.webapp.backend.models import Server
from .server import router as serverRouter

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
)
router.include_router(serverRouter)

@router.get("")
def get_servers(request: Request) -> list[Server]:
    manager: ServerManager = request.app.state.server_manager
    return [server.as_dict() for server in manager.servers]

