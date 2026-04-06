from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.controllers.jobs_controller import router as jobs_router

app = FastAPI(title="Minutes Workflow Agent API", version="0.1.0")
app.include_router(jobs_router)


@app.exception_handler(Exception)
async def generic_exception_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"code": "internal_error", "message": str(exc)})
