import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
import urllib.parse
from sse_starlette import EventSourceResponse

from app.management.manager import ServerManager
from app.management.server import GameConsoleLine, GameServer

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

# TODO move these to some sort of config file
MESSAGE_STREAM_DELAY = 1 # in seconds
MESSAGE_STREAM_RETRY_TIMEOUT = 15000 # in milliseconds

@router.get('/console/stream')
async def console_stream(server: ServerDependency, request: Request):
    async def event_generator():
        events = []
        def add_line(line: GameConsoleLine):
            events.append(line)
        server.console.add_line_listener(add_line)
        last_status = server.status
        while True:
            if await request.is_disconnected():
                # TODO add way to remove listeners besides just directly modifying the list
                server.console.listeners.remove(add_line)
                break

            if last_status != server.status:
               events.append({"event": "status", "data": json.dumps({"status": server.status.name})})

            while events:
                event = events.pop(0)
                yield {
                    # TODO does this event need to have an id field?
                    "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                    **event
                }

            await asyncio.sleep(MESSAGE_STREAM_DELAY)
    # the headers are there because otherwise the React dev server proxy applies compression,
    # causing the front end EventSource to just not work
    return EventSourceResponse(event_generator(), headers={"Cache-Control": "no-cache, no-transform"})
