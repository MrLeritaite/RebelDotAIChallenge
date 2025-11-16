"""
Celery tasks module for RebelDotAIChallenge.

This module provides background task processing capabilities using Celery.
"""

from rebeldotaichallenge.tasks.celery_app import celery_app
from rebeldotaichallenge.tasks.worker_tasks import (
    classify_question_task,
    compliance_response_task,
    health_check_task,
    process_question_task,
)

__all__ = [
    "celery_app",
    "classify_question_task",
    "compliance_response_task",
    "process_question_task",
    "health_check_task",
]
