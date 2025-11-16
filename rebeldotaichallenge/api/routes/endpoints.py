from fastapi import APIRouter

from rebeldotaichallenge.api.routes.tasks_route import task_router

api_router = APIRouter()

api_router.include_router(task_router, prefix="/tasks", tags=["Tasks"])
