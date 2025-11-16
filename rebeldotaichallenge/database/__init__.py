import os
from functools import lru_cache

from rebeldotaichallenge._params import DATABASE_URL
from rebeldotaichallenge.database.pg_vector import LangChainPGVectorStore


@lru_cache(maxsize=1)
def get_default_collection() -> LangChainPGVectorStore:
    return LangChainPGVectorStore(
        connection_string=DATABASE_URL,
        collection_name="default",
        pre_delete_collection=False,
    )


@lru_cache(maxsize=1)
def get_extended_collection() -> LangChainPGVectorStore:
    return LangChainPGVectorStore(
        connection_string=DATABASE_URL,
        collection_name="extended",
        pre_delete_collection=True,
    )
