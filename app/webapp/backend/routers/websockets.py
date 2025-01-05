from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
import jwt

from app.management.manager import ServerManager
from app.management.wizard import CancelledError, ValidationError, WebsocketWizard, StringInput, InputRequest

from ..auth import ALGORITHM

async def auth_websocket(websocket: WebSocket):
    """
    Accepts a websocket and expects the first message it sends to be an access token.
    If the first message is not a valid token the connection is closed.
    """
    token_secret = websocket.app.state.server_manager.env_config.TOKEN_SECRET
    token = await websocket.receive_text()
    credentials_exception = WebSocketException(3000, "Invalid Credentials")
    try:
        payload = jwt.decode(token, token_secret, [ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_exception
    return payload


router = APIRouter(prefix="/ws", tags=["websockets"])

@router.websocket("/servers/create")
async def create_server_interactive(websocket: WebSocket):
    manager: ServerManager = websocket.app.state.server_manager
    await websocket.accept()
    await auth_websocket(websocket)
    try:
        wizard = WebsocketWizard(websocket)
        def ensure_no_server(args):
            if manager.get_server(*args) is not None:
                raise ValidationError("Server already exists!")
        game, id = await wizard.input_multiple(
            InputRequest("Game?", StringInput()),
            InputRequest("ID?", StringInput()),
            validators=[ensure_no_server]
        )
        await manager.create_server(game, id, wizard)
    except (WebSocketDisconnect, CancelledError) as error:
        pass # add debug statement here for when I setup propper logging
