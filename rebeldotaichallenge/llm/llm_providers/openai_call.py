from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rebeldotaichallenge._params import OPENAI_API_KEY, OPENAI_MODEL_ID
from rebeldotaichallenge.schema.API_schema import QuestionClassification

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY),
    model=OPENAI_MODEL_ID,
    temperature=0,
    max_tokens=150,
)
classifier_llm = llm.with_structured_output(QuestionClassification)
