from langchain.tools import tool
from sql_executor.executor import SQLExecutor
from sql_executor.schema_cache import SchemaCache
from guardrails.validator import Guardrails
from orchestrator.chains import get_regeneration_chain

# Initialize guardrails and schema cache
guard = Guardrails()
schema_cache = SchemaCache()
schema_cache.load_schema()  # preload all tables/columns

@tool("run_sql", return_direct=True)
def run_sql_tool(query: str) -> dict:
    executor = SQLExecutor()  # create a new instance each time to avoid stale connections
    return executor.run_query(query)

@tool("guardrails", return_direct=True)
def guardrails_tool(query: str) -> str:
    result = guard.validate(query)
    if not result["ok"]:
        return f"Invalid SQL: {result['errors']}"
    return "VALID"

@tool("regenerate_sql", return_direct=True)
def regenerator_tool(nl_query: str, bad_sql: str, errors: str, schema: str | None = None) -> str:
    """
    Fix SQL queries that fail guardrails or execution.
    Schema information can be used to guide the LLM.
    """
    chain = get_regeneration_chain()
    
    # Build schema string for prompt
    if schema is None:
        schema_dict = schema_cache.get_schema()
        schema_lines = []
        for table, cols in schema_dict.items():
            schema_lines.append(f"{table}: {', '.join(cols)}")
        schema = "\n".join(schema_lines)
    
    return chain.invoke({
        "nl_query": nl_query,
        "bad_sql": bad_sql,
        "errors": errors,
        "schema": schema
    })
