from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import agent_router
from app.settings import get_api_title, get_api_version, get_cors_origins

app = FastAPI(title=get_api_title(), version=get_api_version())

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api")
