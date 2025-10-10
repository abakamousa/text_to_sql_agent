from langchain.tools import tool
from backend.sql_executor.executor import SQLExecutor
from backend.sql_executor.schema_cache import SchemaCache
from backend.guardrails.validator import Guardrails
from backend.sql_generator.generator import SQLGenerator
from backend.regenerator.fixer import SQLRegenerator
import json
import logging

guard = Guardrails()
schema_cache = SchemaCache()

@tool("sql_generator", return_direct=True)
def sql_generator(input_str: str) -> str:
    """Generate SQL from a natural language query."""
    generator = SQLGenerator()
    return generator.generate(nl_query=input_str)


@tool("run_sql_tool", return_direct=True)
def run_sql_tool(query: str) -> dict:
    """Execute a SQL query against the database."""
    executor = SQLExecutor()
    return executor.run_query(query)


@tool("guardrails_tool", return_direct=True)
def guardrails_tool(query: str) -> str:
    """Validate the SQL query using guardrails."""
    result = guard.validate(query)
    if not result["ok"]:
        return f"Invalid SQL: {result['errors']}"
    return "VALID"


@tool("regenerator_tool", return_direct=True)
def regenerator_tool(input_str: str) -> str:
    """Fix invalid SQL queries based on context and errors."""
    try:
        data = json.loads(input_str)
    except json.JSONDecodeError as e:
        return f"Error decoding JSON input: {e}"

    nl_query = data.get("nl_query", "")
    bad_sql = data.get("bad_sql", "")
    errors = data.get("errors", "")
    schema = data.get("schema")

    regenerator = SQLRegenerator()

    if schema is None:
        try:
            schema_dict = schema_cache.get_schema()
        except Exception as e:
            logging.error(f"Failed to get schema for regeneration: {e}")
            schema_dict = {}
        schema_lines = [f"{table}: {', '.join(cols)}" for table, cols in schema_dict.items()]
        schema = "\n".join(schema_lines)

    return regenerator.regenerate(nl_query, bad_sql, errors, schema)
