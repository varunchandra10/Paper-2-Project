from fastapi import APIRouter
from app.api.v1.endpoints import auth, papers, pipeline, chat, telemetry, hardware, models

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(papers.router, tags=["Papers"])
api_router.include_router(pipeline.router, tags=["Pipeline"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(telemetry.router, tags=["Telemetry & Evals"])
api_router.include_router(hardware.router, tags=["Hardware"])
api_router.include_router(models.router, tags=["Inference Models"])
