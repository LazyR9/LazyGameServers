from typing import Annotated
from fastapi import Depends, Request

from app.management.manager import ServerManager


def manager_dependency(request: Request):
    return request.app.state.server_manager
ManagerDependency = Annotated[ServerManager, Depends(manager_dependency)]