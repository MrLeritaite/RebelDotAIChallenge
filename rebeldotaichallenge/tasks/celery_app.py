import logging

from celery import Celery

from rebeldotaichallenge._params import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "rebeldotaichallenge",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["rebeldotaichallenge.tasks.worker_tasks"],
)

logger.info("Celery app configured successfully")
