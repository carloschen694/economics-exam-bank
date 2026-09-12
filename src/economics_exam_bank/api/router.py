from fastapi import APIRouter
from .v1.exams import router as exams_router
from .v1.health import router as health_router
from .v1.practice import router as practice_router
from .v1.questions import router as questions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(exams_router)
api_router.include_router(questions_router)
api_router.include_router(practice_router)
