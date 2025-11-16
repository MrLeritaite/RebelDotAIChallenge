import json
import os

from langchain_core.documents import Document

from rebeldotaichallenge.database import get_default_collection


def add_default_data():
    # Use absolute path that works in Docker container
    data_file_path = os.path.join("/app", ".data", "rag_data", "data.json")

    # Fallback to relative path for local development
    if not os.path.exists(data_file_path):
        data_file_path = os.path.join(".data", "rag_data", "data.json")

    with open(data_file_path, "r") as f:
        data = json.load(f)

    get_default_collection().add_documents(
        [
            Document(page_content=item["question"], metadata={"answer": item["answer"]})
            for item in data["data"]
        ]
    )


if __name__ == "__main__":
    add_default_data()
    print(get_default_collection().get_collection_stats("default"))
