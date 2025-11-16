from typing import Literal

from pydantic import BaseModel, Field


class QuestionClassification(BaseModel):
    """Classify if a user question is IT related"""

    classification: Literal["IT", "non-IT"] = Field(
        ..., description="Classify the question into IT or non-IT."
    )
