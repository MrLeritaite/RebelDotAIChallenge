import hashlib
import json
import logging
import os
from typing import Dict, Optional

from rebeldotaichallenge._params import CACHE_DIR

logger = logging.getLogger(__name__)


os.makedirs(CACHE_DIR, exist_ok=True)


def generate_cache_key(
    query: str,
    model_id: str,
) -> str:
    """
    Generate a cache key for PGVector.

    Args:
        query: The query string
        model_id: The model ID

    Returns:
        Cache key string
    """
    # Convert to string for hashing
    prompt_str = json.dumps(query, sort_keys=True)

    # Create a unique hash based on all parameters
    hash_input = f"{prompt_str}_{model_id}"
    content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
    return f"pgv_{content_hash}_{model_id}"


def generate_cache_filepath(
    query: str,
    model_id: str,
) -> str:
    """
    Generate a cache file path for PGVector.

    Args:
        query: The query string
        model_id: The model ID

    Returns:
        Full path to cache file
    """
    cache_key = generate_cache_key(query, model_id)
    cache_filename = f"{cache_key}.json"

    return os.path.join(CACHE_DIR, cache_filename)


def save_to_cache(cache_filepath: str, response_data: Dict) -> None:
    """
    Save response to cache.

    Args:
        cache_filepath: Path to cache file
        response_data: Response data to cache
    """
    try:
        os.makedirs(os.path.dirname(cache_filepath), exist_ok=True)
        with open(cache_filepath, "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        logger.warning(f"Error writing to cache file: {e}")


def load_cached_response(cache_filepath: str) -> Optional[Dict]:
    """
    Load cached response if available.

    Args:
        cache_filepath: Path to cache file

    Returns:
        Cached response data if available, None otherwise
    """
    try:
        if os.path.isfile(cache_filepath):
            with open(cache_filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Error reading cache file: {e}")
    return None
