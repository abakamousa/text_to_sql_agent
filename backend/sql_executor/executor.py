import pyodbc
import time
from models.settings import settings

class SQLExecutor:
    """
    Executes SQL queries against Azure SQL Database.
    Returns results as list of dicts.
    """

    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string or settings.sql_connection_string
        if not self.connection_string:
            raise ValueError("SQL connection string is not set in environment or settings.")

    def run_query(self, sql: str) -> dict:
        """
        Execute SQL and return structured results.
        Returns:
            {
                "sql": str,
                "rows": List[Dict[str, Any]],
                "row_count": int,
                "execution_time": float (seconds)
            }
        """
        start_time = time.time()
        rows = []

        try:
            with pyodbc.connect(self.connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    for row in cursor.fetchall():
                        rows.append(dict(zip(columns, row)))

        except Exception as e:
            raise RuntimeError(f"SQL execution failed: {e}") from e

        execution_time = time.time() - start_time
        return {
            "sql": sql,
            "rows": rows,
            "row_count": len(rows),
            "execution_time": execution_time
        }


# Singleton-style instance (optional)
executor = SQLExecutor()
def run_query(sql: str) -> dict:
    """Convenience function for tools/orchestrator."""
    return executor.run_query(sql)
