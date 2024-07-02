from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class Metadata(BaseModel, Generic[T]):
    type: str
    flags: int
    value: T

class ServerStats(BaseModel):
    cpu: float
    memory: int

class Server(BaseModel):
    game: Metadata[str]
    id: Metadata[str]
    stats: Metadata[ServerStats]
    status: Metadata[str]
    server_data: Metadata[dict]
