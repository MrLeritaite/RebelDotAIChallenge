import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable must be set")
    return value


def _optional_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value is not None else default


API_KEY = _require_env("API_KEY")
OPENAI_API_KEY = _require_env("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL_ID = "text-embedding-3-small"
OPENAI_MODEL_ID = "gpt-4o-mini"
CACHE_DIR = _require_env("CACHE_DIR")

# Celery Configuration
REDIS_URL = _require_env("REDIS_URL")
CELERY_BROKER_URL = _optional_env("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = _optional_env("CELERY_RESULT_BACKEND", REDIS_URL)

# Database Configuration
DATABASE_URL = _require_env("DATABASE_URL")
