from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.management.manager import ServerManager

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
)

# TODO move these to their own file (models.py or schemas.py or something)
class ServerStats(BaseModel, extra='allow'):
    # TODO should cpu usage be an int percentage or just a 0-1 float?
    cpu: int
    memory: int

class Server(BaseModel, extra='allow'):
    game: str
    id: str
    stats: ServerStats

@router.get("")
def get_servers(request: Request) -> list[Server]:
    manager: ServerManager = request.app.state.server_manager
    return [server.as_dict() for server in manager.servers]

@router.get("/{type:path}/{id}")
def get_server(type: str, id: str, request: Request, response: Response):
    manager: ServerManager = request.app.state.server_manager
    server = manager.get_server(type, id)
    if server is None:
        response.status_code = 404
        return {"error": "404"}
    return server.as_dict()
