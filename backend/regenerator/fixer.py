from backend.sql_executor.schema_cache import SchemaCache
from backend.guardrails.validator import Guardrails
from backend.orchestrator.chains import get_regeneration_chain

class SQLRegenerator:
    """
    Class responsible for regenerating/fixing SQL queries
    that fail guardrails or execution.
    """

    def __init__(self, guard: Guardrails | None = None, schema_cache: SchemaCache | None = None):
        self.guard = guard or Guardrails()
        self.schema_cache = schema_cache or SchemaCache()
        # Preload schema to guide regeneration
        self.schema_cache.load_schema()

    def regenerate(
        self,
        nl_query: str,
        bad_sql: str,
        errors: str,
        schema: str | None = None
    ) -> str:
        """
        Regenerate/fix SQL query using LangChain.
        If schema is not provided, use cached schema.
        """
        chain = get_regeneration_chain()

        # Build schema string for prompt
        if schema is None:
            schema_dict = self.schema_cache.get_schema()
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

    def validate_and_regenerate(self, nl_query: str, bad_sql: str, errors: str) -> str:
        """
        Optional convenience method: first validate the bad SQL and then regenerate.
        """
        validation = self.guard.validate(bad_sql)
        if validation["ok"]:
            # No issues detected, return original
            return bad_sql
        else:
            # Regenerate SQL
            return self.regenerate(nl_query, bad_sql, errors)
