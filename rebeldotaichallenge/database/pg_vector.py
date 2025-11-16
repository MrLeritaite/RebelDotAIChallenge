import logging
import uuid
from typing import Any, Dict, List, Optional

import numpy as np

# LangChain imports
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import SecretStr
from sqlalchemy import text

from rebeldotaichallenge._params import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL_ID
from rebeldotaichallenge.database.pg_vector_helpers import (
    generate_cache_filepath,
    load_cached_response,
    save_to_cache,
)
from rebeldotaichallenge.schema.database_schema import EmbeddingDocument, SearchResult

logger = logging.getLogger(__name__)


class LangChainPGVectorStore:
    """
    LangChain-compatible wrapper for PGVector with enhanced functionality.

    This class provides a bridge between the custom PGVectorStore implementation
    and LangChain's VectorStore interface, offering the best of both worlds.
    """

    def __init__(
        self,
        connection_string: str,
        collection_name: str = "default",
        pre_delete_collection: bool = False,
    ):
        """
        Initialize LangChain-compatible PGVector store.

        Args:
            connection_string: PostgreSQL connection string
            collection_name: Name of the collection
            pre_delete_collection: Whether to delete existing collection
        """
        # Use OpenAI embeddings as default
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")

        self.embeddings = OpenAIEmbeddings(
            model=OPENAI_EMBEDDING_MODEL_ID,
            api_key=SecretStr(OPENAI_API_KEY),
        )

        # Initialize LangChain PGVector
        self.langchain_store = PGVector(
            connection=connection_string,
            embeddings=self.embeddings,
            collection_name=collection_name,
            pre_delete_collection=pre_delete_collection,
        )

    def add_documents(self, documents: List[Document], **kwargs: Any) -> List[str]:
        """
        Add LangChain documents to the vector store.

        Args:
            documents: List of LangChain Document objects
            **kwargs: Additional arguments

        Returns:
            List of document IDs
        """
        documents_to_save = []
        ids = []
        all_ids = []

        for doc in documents:
            cache_filepath = generate_cache_filepath(
                query=doc.page_content, model_id=OPENAI_EMBEDDING_MODEL_ID
            )
            cached_data = load_cached_response(cache_filepath)

            if cached_data:
                # Cache hit: extract the persisted ID from cached payload
                cached_doc_id = cached_data.get("document_id")
                if cached_doc_id:
                    all_ids.append(cached_doc_id)
                    logger.info(
                        f"The document is already in the cache with ID {cached_doc_id}. Skipping database insertion."
                    )
                else:
                    # Handle legacy cache entries without document_id
                    logger.warning(
                        f"Cached document found but no document_id present. This is a legacy cache entry."
                    )
                    # Generate new ID and treat as cache miss
                    doc_id = str(uuid.uuid4())
                    all_ids.append(doc_id)
                    doc_data = {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    save_to_cache(
                        cache_filepath, {"document": doc_data, "document_id": doc_id}
                    )
                    documents_to_save.append(doc)
                    ids.append(doc_id)
            else:
                # Cache miss: generate new UUID and save to both cache and database
                doc_id = str(uuid.uuid4())
                all_ids.append(doc_id)
                ids.append(doc_id)

                logger.info(
                    f"The document is not in the cache. Adding to database with ID {doc_id}."
                )
                doc_data = {"page_content": doc.page_content, "metadata": doc.metadata}
                save_to_cache(
                    cache_filepath, {"document": doc_data, "document_id": doc_id}
                )
                documents_to_save.append(doc)

        # Only add documents that are not cached
        if documents_to_save:
            return self.langchain_store.add_documents(
                documents_to_save, ids=ids, **kwargs
            )
        return all_ids

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """
        Perform similarity search with scores using LangChain interface.

        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
            **kwargs: Additional arguments

        Returns:
            List of SearchResult objects
        """
        # Get raw results from LangChain store
        raw_results = self.langchain_store.similarity_search_with_score(
            query=query, k=k, filter=filter, **kwargs
        )

        # Convert to SearchResult objects
        search_results = []
        for rank, (document, score) in enumerate(raw_results, 1):
            # Convert LangChain Document to EmbeddingDocument
            embedding_doc = EmbeddingDocument(
                content=document.page_content,
                metadata=document.metadata,
                collection_name=self.langchain_store.collection_name,
            )

            # Create SearchResult
            search_result = SearchResult(
                document=embedding_doc,
                similarity_score=score,
                rank=rank,
            )
            search_results.append(search_result)

        return search_results

    def update_document_metadata(
        self,
        document_id: str,
        new_metadata: Dict[str, Any],
        preserve_content: bool = True,
    ) -> bool:
        """
        Update metadata for a specific document without changing its content.

        Args:
            document_id: ID of the document to update
            new_metadata: New metadata to set
            preserve_content: If True, preserves the original content and only updates metadata

        Returns:
            True if document was found and updated, False otherwise
        """
        try:
            # Get the existing document
            existing_docs = self.langchain_store.get_by_ids([document_id])

            if not existing_docs:
                logger.warning(f"Document with ID {document_id} not found")
                return False

            existing_doc = existing_docs[0]

            if preserve_content:
                self.langchain_store.add_documents(
                    [
                        Document(
                            page_content=existing_doc.page_content,
                            metadata=new_metadata,
                        )
                    ],
                    ids=[document_id],
                )
            else:
                raise ValueError(
                    "preserve_content=False requires providing new content"
                )

            return True

        except Exception as e:
            logger.error(f"Error updating document metadata: {e}")
            return False

    def get_documents_by_ids(self, ids: List[str]) -> List[Document]:
        """
        Retrieve documents by their IDs.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            List of Document objects
        """
        return self.langchain_store.get_by_ids(ids)

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete
        """
        self.langchain_store.delete(ids=ids)

    def get_collection_info_from_db(self) -> dict:
        from sqlalchemy import text

        with self.langchain_store._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM langchain_pg_collection WHERE name = :name"),
                {"name": self.langchain_store.collection_name},
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def get_collection_stats(self, collection_name: str) -> dict:

        with self.langchain_store._engine.connect() as conn:
            # Get collection row
            coll = conn.execute(
                text(
                    "SELECT uuid, cmetadata FROM langchain_pg_collection WHERE name = :name"
                ),
                {"name": collection_name},
            ).fetchone()
            if not coll:
                return {"error": f"Collection '{collection_name}' not found"}

            collection_id = coll.uuid

            # Count documents
            doc_count = conn.execute(
                text(
                    "SELECT COUNT(*) FROM langchain_pg_embedding WHERE collection_id = :cid"
                ),
                {"cid": collection_id},
            ).scalar()

            # Optionally list IDs
            doc_ids = conn.execute(
                text(
                    "SELECT id FROM langchain_pg_embedding WHERE collection_id = :cid LIMIT 20"
                ),
                {"cid": collection_id},
            ).fetchall()

            return {
                "collection_id": str(collection_id),
                "metadata": coll.cmetadata,
                "document_count": doc_count,
                "sample_doc_ids": [r.id for r in doc_ids],
            }

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete an entire collection and all of its documents.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if the collection was deleted, False if not found
        """
        try:
            with self.langchain_store._engine.begin() as conn:
                # Get the collection UUID
                result = conn.execute(
                    text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
                    {"name": collection_name},
                ).fetchone()

                if not result:
                    logger.warning(f"Collection '{collection_name}' not found")
                    return False

                collection_id = result.uuid

                # Delete all documents for that collection
                conn.execute(
                    text(
                        "DELETE FROM langchain_pg_embedding WHERE collection_id = :cid"
                    ),
                    {"cid": collection_id},
                )

                # Delete the collection itself
                conn.execute(
                    text("DELETE FROM langchain_pg_collection WHERE uuid = :cid"),
                    {"cid": collection_id},
                )

                logger.info(f"Collection '{collection_name}' and its documents deleted")
                return True

        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            return False


if __name__ == "__main__":
    db = LangChainPGVectorStore(
        connection_string="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
        collection_name="test",
    )

    db.add_documents(
        [
            Document(page_content="2", metadata={"id": "1"}),
            Document(page_content="6", metadata={"id": "2"}),
        ]
    )
    print(db.similarity_search_with_score("4", k=2))

    print(db.get_collection_info_from_db())
    print(db.get_collection_stats("test"))
