from fastapi import APIRouter, Depends

from ..dependencies import ManagerDependency
from ..models import Server
from .server import router as serverRouter
from ..auth import get_current_user

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
    dependencies=[Depends(get_current_user)]
)
router.include_router(serverRouter)

@router.get("")
def get_servers(manager: ManagerDependency) -> list[Server]:
    return [server.as_dict(True) for server in manager.servers]

@router.post("")
def create_server(body: dict, manager: ManagerDependency):
    server = manager.create_server(body["type"], body["id"])
    return server.as_dict(True)
