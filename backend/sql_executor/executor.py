import pyodbc
import datetime
from backend.models.settings import settings

class SQLExecutor:
    """Executes SQL queries against Azure SQL Database."""

    def __init__(self):
        self.conn_str = settings.sql_connection_string

    def run_query(self, sql: str) -> dict:
        """Run a SQL query and return rows as list of dicts with JSON-serializable values."""
        try:
            with pyodbc.connect(self.conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()

                result = []
                for row in rows:
                    row_dict = {}
                    for col, val in zip(columns, row):
                        # Convert datetime/date to ISO string
                        if isinstance(val, (datetime.datetime, datetime.date)):
                            row_dict[col] = val.isoformat()
                        else:
                            row_dict[col] = val
                    result.append(row_dict)

                return {
                    "rows": result,
                    "row_count": len(result),
                }

        except Exception as e:
            raise RuntimeError(f"SQL execution failed: {e}") from e
