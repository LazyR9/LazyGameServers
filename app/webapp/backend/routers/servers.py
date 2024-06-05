from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.management.manager import ServerManager
from .server import router as serverRouter

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
)
router.include_router(serverRouter)

# TODO move these to their own file (models.py or schemas.py or something)
class ServerStats(BaseModel, extra='allow'):
    cpu: float
    memory: int

class Server(BaseModel, extra='allow'):
    game: str
    id: str
    stats: ServerStats

@router.get("")
def get_servers(request: Request) -> list[Server]:
    manager: ServerManager = request.app.state.server_manager
    return [server.as_dict() for server in manager.servers]

