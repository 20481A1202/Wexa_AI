import structlog
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import get_settings
from app.core.security import decode_token
from app.db.session import init_db
from app.services.realtime import realtime_manager

settings = get_settings()
logger = structlog.get_logger()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    await init_db()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api_router)


@app.websocket("/ws/events/{organization_id}")
async def events_websocket(websocket: WebSocket, organization_id: str):
    token = websocket.query_params.get("token")
    try:
        payload = decode_token(token or "")
        if payload.get("organization_id") != organization_id:
            await websocket.close(code=1008)
            return
    except ValueError:
        await websocket.close(code=1008)
        return
    await realtime_manager.connect(organization_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_manager.disconnect(organization_id, websocket)
