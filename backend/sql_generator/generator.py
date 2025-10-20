import json
import logging
from backend.sql_executor.schema_cache import SchemaCache
from backend.services.openai_client import OpenAIClient


class SQLGenerator:
    """
    Generates SQL queries from natural language using an LLM,
    enriched with table schemas and table descriptions from SchemaCache.
    """

    def __init__(self):
        self.llm = OpenAIClient().get_llm()
        self.schema_cache = SchemaCache()

    def _build_schema_context(self) -> str:
        """
        Build a text context of all tables and columns for LLM prompt.
        """
        schema_dict = self.schema_cache.get_schema()
        context_lines = []
        for table_name, info in schema_dict.items():
            description = info.get("description", "No description available.")
            columns = ", ".join(info.get("columns", []))
            context_lines.append(f"Table: {table_name}\nDescription: {description}\nColumns: {columns}\n")
        return "\n".join(context_lines)


    def generate(self, nl_query: str) -> str:
        """
        Generate an SQL query from a natural language question using LLM.
        Includes schema and table descriptions in context.
        """
        try:
            schema_context = self._build_schema_context()

            prompt = f"""
            You are a data analyst and SQL expert.
            Your task is to generate a correct, optimized SQL query based on the user’s natural language request.

            Here is the database schema and table descriptions:

            {schema_context}

            Follow these rules:
            - Only use tables and columns that exist in the schema above.
            - Use proper JOINs if relationships are implied.
            - Do not hallucinate table or column names.
            - Return ONLY the SQL query, no explanation.

            User request:
            {nl_query}
            """

            logging.info("🧠 Generating SQL for NL query: %s", nl_query)
            response = self.llm.invoke(prompt)

            # Handle response variations depending on LLM API
            if isinstance(response, dict) and "content" in response:
                return response["content"].strip()
            elif hasattr(response, "content"):
                return response.content.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                logging.warning(" Unexpected LLM response type: %s", type(response))
                return str(response)

        except Exception as e:
            logging.exception(f"SQL generation failed: {e}")
            return f"Error generating SQL: {str(e)}"
