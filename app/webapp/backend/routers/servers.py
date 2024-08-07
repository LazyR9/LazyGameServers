from fastapi import APIRouter, Depends

from ..dependencies import ManagerDependency
from ..models import Server
from .server import router as serverRouter

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
)
router.include_router(serverRouter)

@router.get("")
def get_servers(manager: ManagerDependency) -> list[Server]:
    return [server.as_dict(True) for server in manager.servers]

@router.post("")
def create_server(body: dict, manager: ManagerDependency):
    server = manager.create_server(body["type"], body["id"])
    return server.as_dict(True)
