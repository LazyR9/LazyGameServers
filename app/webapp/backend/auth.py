import os
from fastapi import Depends, HTTPException, APIRouter, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from typing import Annotated
from pydantic import BaseModel

from .routers.servers import ManagerDependency

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 15

# workaround for passlib because it is no longer updated and tries to access bcrypt.__about__.__version__
# this just silences that error
import bcrypt
bcrypt.__about__ = lambda: None
bcrypt.__about__.__version__ = "workaround"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

def get_token_secret(manager: ManagerDependency):
    return manager.env_config.TOKEN_SECRET
TokenSecret = Annotated[str, Depends(get_token_secret)]

def create_token(data: dict, secret_key, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, ALGORITHM)
    
def create_user_access_token(user, secret_key):
    access_token = create_token({"sub": user}, secret_key, timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES))
    return Token(access_token=access_token, token_type="bearer")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], token_secret: TokenSecret):
    credentials_exception = HTTPException(401, "Invalid Credentials", {"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, token_secret, [ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_exception
    return payload
    

class Token(BaseModel):
    access_token: str
    token_type: str

class SetPasswordBody(BaseModel):
    old_password: str | None
    new_password: str

@router.post("/login")
async def login_for_refresh_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], manager: ManagerDependency,
                                  token_secret: TokenSecret, response: Response) -> Token:
    hashed_password = manager.config.password_hash
    if not pwd_context.verify(form_data.password, hashed_password):
        raise HTTPException(401, "Incorrect password", {"WWW-Authenticate": "Bearer"})
    refresh_token = create_token({"sub": "admin"}, token_secret, timedelta(days=1))
    response.set_cookie("refresh_token", refresh_token, 60*60*24, httponly=True)
    
    return create_user_access_token("admin", token_secret)

@router.post("/logout")
async def logout(request: Request, response: Response):
    if "refresh_token" in request.cookies:
        response.delete_cookie("refresh_token")

@router.post("/refresh")
async def refresh(request: Request, token_secret: TokenSecret):
    exception = HTTPException(401, "Invalid refresh token!")
    if "refresh_token" not in request.cookies:
        raise exception
    refresh_token = request.cookies["refresh_token"]
    try:
        payload = jwt.decode(refresh_token, token_secret, [ALGORITHM])
    except jwt.InvalidTokenError:
        raise exception
    return create_user_access_token(payload["sub"], token_secret)

async def optional_auth(request: Request):
    oauth2_scheme.auto_error = False
    token = await oauth2_scheme(request)
    oauth2_scheme.auto_error = True
    return token

@router.put("/password")
async def set_password(token: Annotated[str, Depends(optional_auth)], server_manager: ManagerDependency,
                       token_secret: TokenSecret, body: SetPasswordBody):
    password_hash = server_manager.config.password_hash
    # only require authentication if password is set,
    # that way we can use this endpoint during first time setup when there is no password
    if password_hash is not None:
        await get_current_user(token, token_secret)
        if not pwd_context.verify(body.old_password, password_hash):
            raise HTTPException(401, "Incorrect password", {"WWW-Authenticate": "Bearer"})
    server_manager.config.password_hash = pwd_context.hash(body.new_password)

