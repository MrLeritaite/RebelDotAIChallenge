import logging
import time
from typing import Any, Dict, Literal

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from rebeldotaichallenge._params import OPENAI_EMBEDDING_MODEL_ID
from rebeldotaichallenge.database import get_default_collection, get_extended_collection
from rebeldotaichallenge.database.pg_vector_helpers import (
    generate_cache_filepath,
    load_cached_response,
    save_to_cache,
)
from rebeldotaichallenge.llm.llm_providers.openai_call import classifier_llm, llm
from rebeldotaichallenge.tasks.celery_app import celery_app
from rebeldotaichallenge.utils.prompts import (
    ANSWER_QUESTION_PROMPT,
    CLASSIFY_QUESTION_PROMPT,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_question_task")
def process_question_task(
    self, question: str, collection_name: str = "default", **kwargs
) -> Dict[str, Any]:
    """
    Process a question using vector similarity search.

    Args:
        question: The question to process
        collection_name: Name of the vector collection to search
        **kwargs: Additional parameters

    Returns:
        Dictionary containing the results
    """
    try:
        task_id = self.request.id
        logger.info(
            f"Starting question processing task {task_id} for question: {question[:100]}..."
        )

        # Perform similarity search in default collection
        search_results = get_default_collection().similarity_search_with_score(
            query=question, k=kwargs.get("k", 1)
        )

        # Check if similarity score is below threshold
        if search_results and search_results[0].similarity_score < 0.4:
            return {
                "source": "local",
                "matched_question": search_results[0].document.content,
                "answer": search_results[0].document.metadata["answer"],
            }
        else:
            # Check if cached result exists
            filepath = generate_cache_filepath(
                query=question, model_id=OPENAI_EMBEDDING_MODEL_ID
            )
            cached_data = load_cached_response(filepath)
            if cached_data:
                return {
                    "source": "openai",
                    "matched_question": "N/A",
                    "answer": cached_data["document"]["metadata"]["answer"],
                }
            else:
                # Try to find answer in extended collection first
                try:
                    if (
                        get_extended_collection().get_collection_stats(
                            collection_name="extended"
                        )["document_count"]
                        > 0
                    ):
                        search_results_extended = (
                            get_extended_collection().similarity_search_with_score(
                                query=question, k=kwargs.get("k", 1)
                            )
                        )
                        if (
                            search_results_extended
                            and search_results_extended[0].similarity_score < 0.4
                        ):
                            return {
                                "source": "openai",
                                "matched_question": "N/A",
                                "answer": search_results_extended[0].document.metadata[
                                    "answer"
                                ],
                            }

                except Exception as e:
                    logger.error(f"Error in extended collection search: {e}")
                    # Continue to LLM fallback

                # If no cached result found, use LLM to generate answer
                llm_prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            ANSWER_QUESTION_PROMPT,
                        ),
                        (
                            "human",
                            "Answer the following question briefly: {question}",
                        ),
                    ]
                )
                formatted = llm_prompt.invoke({"question": question})
                response = llm.invoke(formatted)

                save_to_cache(filepath, {"answer": response.content})
                get_extended_collection().add_documents(
                    [
                        Document(
                            page_content=question,
                            metadata={"answer": response.content},
                        )
                    ]
                )

                return {
                    "source": "openai",
                    "matched_question": "N/A",
                    "answer": response.content,
                }

    except Exception as e:
        logger.error(f"Error in question processing task {self.request.id}: {str(e)}")
        self.update_state(state="FAILURE", meta={"error": str(e), "status": "failed"})
        raise


@celery_app.task(bind=True, name="health_check_task")
def health_check_task(self) -> Dict[str, Any]:
    """
    Simple health check task to verify Celery is working.

    Returns:
        Dictionary containing health check results
    """
    try:
        task_id = self.request.id
        logger.info(f"Starting health check task {task_id}")

        # Simulate some work
        time.sleep(1)

        result = {
            "task_id": task_id,
            "status": "healthy",
            "message": "Celery worker is functioning correctly",
            "timestamp": time.time(),
        }

        logger.info(f"Health check task {task_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in health check task {self.request.id}: {str(e)}")
        self.update_state(state="FAILURE", meta={"error": str(e), "status": "failed"})
        raise


# New router task for question classification
@celery_app.task(bind=True, name="classify_question_task")
def classify_question_task(self, question: str) -> Literal["IT", "non-IT"]:
    """
    Classify if question is IT-related using LangChain router
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CLASSIFY_QUESTION_PROMPT),
            ("human", "Classify the following question: {question}"),
        ]
    )

    router = prompt | classifier_llm
    result = router.invoke({"question": question})

    return result.classification


@celery_app.task(bind=True, name="compliance_response_task")
def compliance_response_task(self, question: str) -> Dict[str, Any]:
    """
    Fast compliance response for non-IT questions
    """
    return {
        "matched_question": "N/A",
        "answer": "This is not really what I was trained for, therefore I cannot answer. Try again.",
    }
