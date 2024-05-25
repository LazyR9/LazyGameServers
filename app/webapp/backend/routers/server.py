from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
import urllib.parse

from app.management.manager import ServerManager
from app.management.server import GameServer

router = APIRouter(
    prefix="/{type}/{id}",
)

def server_dependency(type: str, id: str, request: Request, response: Response):
    manager: ServerManager = request.app.state.server_manager
    server = manager.get_server(urllib.parse.unquote(type), id)
    if server is None:
        raise HTTPException(404)
    return server

ServerDependency = Annotated[GameServer, Depends(server_dependency)]

@router.get("")
def get_server(server: ServerDependency):
    return server.as_dict()

# TODO these functions use this as a placeholder until i decide what the API should respond with
temp = {"result": "success"}
@router.get("/start")
def start_server(server: ServerDependency):
    server.start_server()
    return temp

@router.get("/stop")
def stop_server(server: ServerDependency):
    server.stop_server()
    return temp

@router.get("/console")
def get_server_console(server: ServerDependency):
    return server.console.as_dict()

@router.post("/console")
def run_command(server: ServerDependency, command: dict):
    server.send_console_command(command['command'])
    return temp

@router.get('/console/stream')
