from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnableSequence

from backend.models.settings import settings
from backend.sql_executor.schema_cache import SchemaCache
from backend.services.openai_client import OpenAIClient


class SQLGenerator:
    """
    Converts natural language queries into SQL statements
    using an LLM and database schema context.

    This version uses the new LangChain Runnable interface
    instead of the deprecated LLMChain.
    """

    def __init__(self):
        # 🔧 Initialize the OpenAI client via centralized service
        openai_service = OpenAIClient()
        self.llm = openai_service.get_llm()

        self.schema_cache = SchemaCache()

        # Define prompt using the new ChatPromptTemplate
        self.prompt = ChatPromptTemplate.from_template(
            """You are an expert SQL developer.
            Given the following database schema, write a correct SQL query for the user's question.

            Schema:
            {schema}

            Question:
            {nl_query}

            Output only the SQL query, no explanations or comments."""
                    )

        # Build the runnable chain: prompt → model → text output
        self.chain: RunnableSequence = self.prompt | self.llm | StrOutputParser()

    def generate(self, nl_query: str) -> str:
        """Generate SQL text from a natural-language query."""
        schema_dict = self.schema_cache.get_schema()
        if not schema_dict:
            self.schema_cache.load_schema()
            schema_dict = self.schema_cache.get_schema()

        schema_text = "\n".join(
            f"{table}: {', '.join(columns)}" for table, columns in schema_dict.items()
        )

        # Run the sequence
        sql_query = self.chain.invoke({"nl_query": nl_query, "schema": schema_text}).strip()
        return sql_query

    def generate_with_metadata(self, nl_query: str) -> Dict[str, Any]:
        """Return generated SQL and metadata context."""
        schema_dict = self.schema_cache.get_schema()
        if not schema_dict:
            self.schema_cache.load_schema()
            schema_dict = self.schema_cache.get_schema()

        schema_text = "\n".join(
            f"{table}: {', '.join(columns)}" for table, columns in schema_dict.items()
        )

        sql_query = self.chain.invoke({"nl_query": nl_query, "schema": schema_text}).strip()

        return {
            "nl_query": nl_query,
            "schema_used": schema_dict,
            "generated_sql": sql_query,
        }
