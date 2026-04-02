from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_api_title, get_api_version, get_cors_origins
from app.controller.proposal_controller import router as proposal_router

app = FastAPI(title=get_api_title(), version=get_api_version())

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(proposal_router, prefix="/api")
