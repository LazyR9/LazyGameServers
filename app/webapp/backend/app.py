from fastapi import FastAPI

from .routers import servers

app = FastAPI(root_path="/api")

app.include_router(servers.router)
