from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import auth

from .servers import ManagerDependency


class SetupArgs(BaseModel):
    password: str


router = APIRouter(prefix="/setup")

@router.get("")
def check_setup(manager: ManagerDependency):
    return {"setup": manager.config.setup}

@router.put("")
def put_setup(manager: ManagerDependency, args: SetupArgs):
    if manager.config.setup:
        raise HTTPException(409, "Server has already been setup!")
    manager.config.password_hash = auth.pwd_context.hash(args.password)
    manager.config.setup = True
