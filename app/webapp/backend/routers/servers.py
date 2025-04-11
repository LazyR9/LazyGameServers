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

@router.get("", response_model=list[Server])
def get_servers(manager: ManagerDependency):
    return [server.as_dict(True) for server in manager.servers]
