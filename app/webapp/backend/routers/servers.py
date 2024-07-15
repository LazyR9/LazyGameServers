from typing import Annotated
from fastapi import APIRouter, Depends, Request

from app.management.manager import ServerManager
from app.webapp.backend.models import Server
from .server import router as serverRouter

router = APIRouter(
    prefix="/servers",
    tags=["servers"],
)
router.include_router(serverRouter)

def manager_dependency(request: Request):
    return request.app.state.server_manager

ManagerDependency = Annotated[ServerManager, Depends(manager_dependency)]

@router.get("")
def get_servers(manager: ManagerDependency) -> list[Server]:
    return [server.as_dict(True) for server in manager.servers]

@router.post("")
def create_server(body: dict, manager: ManagerDependency):
    server = manager.create_server(body["type"], body["id"])
    return server.as_dict(True)
