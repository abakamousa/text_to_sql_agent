from langchain.tools import tool
from backend.sql_executor.executor import SQLExecutor
from backend.sql_executor.schema_cache import SchemaCache
from backend.guardrails.validator import Guardrails
from backend.sql_generator.generator import SQLGenerator
from backend.regenerator.fixer import SQLRegenerator
from backend.services.openai_client import OpenAIClient
from backend.answer_generator.answer_generator import generate_answer
from backend.visualization.visualisation_recommander import VisualizationRecommender
import json
import logging

# Initialize shared services
guard = Guardrails()
schema_cache = SchemaCache()
logger = logging.getLogger(__name__)


# ========================================
# 🧠 SQL GENERATION
# ========================================
@tool("sql_generator", return_direct=True)
def sql_generator(input_str: str) -> str:
    """Generate SQL from a natural language query."""
    generator = SQLGenerator()
    return generator.generate(nl_query=input_str)


# ========================================
# ⚙️ RUN SQL QUERY
# ========================================
@tool("run_sql_tool", return_direct=True)
def run_sql_tool(query: str) -> dict:
    """Execute a SQL query against the database."""
    executor = SQLExecutor()
    return executor.run_query(query)


# ========================================
# 🧩 GUARDRAILS VALIDATION
# ========================================
@tool("guardrails_tool", return_direct=True)
def guardrails_tool(query: str) -> str:
    """Validate the SQL query using guardrails."""
    result = guard.validate(query)
    if not result["ok"]:
        return f"Invalid SQL: {result['errors']}"
    return "VALID"


# ========================================
# 📊 VISUALIZATION RECOMMENDER 
# ========================================
@tool("visualization_tool", return_direct=True)
def visualization_tool(input_str: str) -> dict:
    """
    Recommend the best visualization for a given query, SQL, and results.
    Input (JSON string):
    {
        "query": "<user question>",
        "sql": "<generated SQL>",
        "data": [ { "col1": ..., "col2": ... }, ... ]
    }

    Output:
    {
        "chart_type": "bar" | "line" | "pie" | "scatter" | "table",
        "x_axis": "<column_name>",
        "y_axis": "<column_name>",
        "title": "<chart title>",
        "reason": "<reason>"
    }
    """
    try:
        data = json.loads(input_str)
    except json.JSONDecodeError as e:
        return {"error": f"Error decoding JSON input: {e}"}

    nl_query = data.get("query")
    sql_query = data.get("sql")
    sql_results = data.get("data")

    try:
        recommender = VisualizationRecommender(nl_query, sql_query, sql_results)
        recommendation = recommender.recommend_chart()
        return recommendation
    except Exception as e:
        logger.exception(f"Visualization recommendation failed: {e}")
        return {"error": str(e)}

# ========================================
# 🔁 SQL REGENERATION (FIXER)
# ========================================
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


# ========================================
# 💬 ANSWER GENERATOR 
# ========================================
@tool("answer_generator_tool", return_direct=True)
def answer_generator_tool(input_str: str) -> str:
    """
    Generate a natural language answer using the SQL query results.
    Input must be a JSON string with keys:
    {
        "nl_query": "<user question>",
        "sql_query": "<generated SQL>",
        "sql_results": "<SQL execution output>"
    }
    """
    #logging.info(f"🧠 Generating answer from LLM. with input: {input_str}"  )
    try:
        data = json.loads(input_str)
    except json.JSONDecodeError as e:
        return f"Error decoding JSON input: {e}"

    nl_query = data.get("query", "")
    sql_query = data.get("data", "")
    sql_results = data.get("sql_results", "")
    #logging.info(f"🧠 Generating answer from LLM. with {nl_query}, {sql_query}, {sql_results}"  )

    try:
        response = generate_answer(nl_query, sql_query, sql_results)
        return response

    except Exception as e:
        logger.exception(f"Error generating LLM answer: {e}")
        return f"Error generating natural language answer: {e}"
