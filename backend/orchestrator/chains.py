from backend.services.openai_client import OpenAIClient
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path


BASE_PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(file: str) -> str:
    return (BASE_PROMPT_DIR / file).read_text()


def get_sql_generation_chain():
    """Chain for generating SQL from natural language."""
    llm = OpenAIClient().get_llm()
    template = load_prompt("generator_prompt.txt")

    prompt = ChatPromptTemplate.from_messages(
        [("system", template), ("user", "{query}")]
    )
    return prompt | llm | StrOutputParser()


def get_regeneration_chain():
    """Chain for regenerating SQL when it fails guardrails or execution."""
    llm = OpenAIClient().get_llm()
    template = load_prompt("regenerator_prompt.txt")

    prompt = ChatPromptTemplate.from_messages(
        [("system", template),
         ("user", "Query: {nl_query}\nBad SQL: {bad_sql}\nErrors: {errors}\nSchema: {schema}")]
    )
    return prompt | llm | StrOutputParser()
