import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
import urllib.parse
from sse_starlette import EventSourceResponse

from app.management.manager import ServerManager
from app.management.server import GameServer, GameServerEvent

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

@router.get('/stream')
async def console_stream(server: ServerDependency, request: Request):
    async def event_generator():
        events: list[GameServerEvent] = []
        def add_to_event_queue(event: GameServerEvent):
            events.append(event)
        listener = server.add_event_listener(add_to_event_queue)

        while True:
            if await request.is_disconnected():
                listener.deregister()
                break

            while events:
                event = events.pop(0)
                yield {
                    # TODO does this event need to have an id field?
                    "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                    "event": event.type.name.lower(),
                    # use data_dict to only get data, as the event type is already encoded in the event
                    # also manually convert to JSON, as that isn't done automatically here for some reason
                    "data": json.dumps(event.data_dict())
                }

            await asyncio.sleep(MESSAGE_STREAM_DELAY)
    # The default for Cache-Control header just has no-cache,
    # but we need no-transform to get the React dev server to not apply compression,
    # because it is hardcoded to be on for some reason,
    # and the EventSource API just doesn't work if the request has compression.
    return EventSourceResponse(event_generator(), headers={"Cache-Control": "no-cache, no-transform"})
