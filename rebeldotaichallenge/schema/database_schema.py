import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmbeddingDocument(BaseModel):
    """Model for embedding documents"""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    collection_name: str = "default"


class SearchResult(BaseModel):
    """Model for search results"""

    document: EmbeddingDocument
    similarity_score: float
    rank: int
