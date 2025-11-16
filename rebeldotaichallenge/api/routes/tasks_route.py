import asyncio
import logging

from fastapi import APIRouter, Depends

from rebeldotaichallenge.tasks import (
    classify_question_task,
    compliance_response_task,
    process_question_task,
)
from rebeldotaichallenge.utils.security_service import SecurityService

task_router = APIRouter(dependencies=[Depends(SecurityService.get_api_key)])
logger = logging.getLogger(__name__)


@task_router.post("/ask_question")
async def create_task(user_question: str) -> dict:
    # Queue the task for background processing
    classification_result = classify_question_task.delay(question=user_question)
    classification = await asyncio.to_thread(classification_result.get, timeout=30)

    if classification == "IT":
        # Route to high-priority queue for complex processing
        task_result = process_question_task.apply_async(
            args=[user_question], queue="high_priority", priority=9
        )
    else:
        # Route to low-priority queue for compliance response
        task_result = compliance_response_task.apply_async(
            args=[user_question], queue="low_priority", priority=1
        )

    logger.info(f"Creating task with ID: {task_result.id}")
    return await asyncio.to_thread(task_result.get, timeout=60)
