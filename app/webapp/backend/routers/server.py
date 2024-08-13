import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, HTTPException
import urllib.parse
from sse_starlette import EventSourceResponse

from app.management.manager import ServerManager
from app.management.server import GameServer, GameServerEvent
from app.management.storage import File, FileType

router = APIRouter(
    prefix="/{type}/{id}",
)

def server_dependency(type: str, id: str, request: Request):
    manager: ServerManager = request.app.state.server_manager
    server = manager.get_server(urllib.parse.unquote(type), urllib.parse.unquote(id))
    if server is None:
        raise HTTPException(404)
    return server

ServerDependency = Annotated[GameServer, Depends(server_dependency)]

def server_file_dependency(server: ServerDependency, path: str):
    file = server.get_directory().get_file_or_dir(path)
    if file is None:
        raise HTTPException(404)
    return file

ServerFileDependency = Annotated[File, Depends(server_file_dependency)]

@router.get("")
def get_server(server: ServerDependency):
    return server.as_dict(True)

@router.put("")
def update_server(server: ServerDependency, body: dict):
    failed_keys = server.update_from_dict(body)
    # TODO change response based if there were any failures or not,
    # i want to add better error reporting on this first tho
    return {
        "failed_keys": failed_keys
    }

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
    # TODO send only part of the console and have more load as the user scrolls up
    return server.console.as_dict()

@router.post("/console")
def run_command(server: ServerDependency, command: dict):
    server.send_console_command(command['command'])
    return temp

# TODO move these to some sort of config file
MESSAGE_STREAM_DELAY = 1 # in seconds
MESSAGE_STREAM_RETRY_TIMEOUT = 15000 # in milliseconds

@router.get('/stream')
async def event_stream(server: ServerDependency, request: Request):
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

# A trailing slash is required with the variable in the route below,
# this is here so that it can be omitted
@router.get('/files')
def get_root_directory(server: ServerDependency):
    return get_file(server, '')

@router.get('/files/{path:path}')
def get_file(file: ServerFileDependency, path):
    # TODO binary files just throw an error here, need to figure out a way to tell that a file is binary
    # TODO add a raw parameter that just sends the file over HTTP instead of wrapping in JSON,
    # which will also be the only way to get contents of binary or large files.
    # TODO add a size limit so that getting the raw file is the only way to get contents.
    # This means that files over that limit cannot be opened in the frontend editor.
    file_dict = file.as_dict(True)
    # append the path used to get to the file, as it is relative to the root
    # and also means the real location on disk doesn't get potentionally leaked.
    # TODO don't just copy the path used to get,
    # because including multiple slashes in the url will still work and then they will be included here.
    file_dict['path'] = "/" + path
    if path in ('', '.'):
        file_dict['name'] = '/'
    return file_dict

@router.put('/files/{path:path}')
def put_file(file: ServerFileDependency, new_file: dict, response: Response):
    if file.type != FileType.FILE:
        raise HTTPException(405)
    if not file.exists():
        response.status_code = 201
    with file.open("w") as writable_file:
        writable_file.write(new_file['contents'])
    return temp
