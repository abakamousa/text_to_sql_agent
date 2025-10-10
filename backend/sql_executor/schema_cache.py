from typing import Dict, List
import pyodbc
import json
import os
from backend.models.settings import settings


class SchemaCache:
    """
    Simple schema cache that loads table/column information from Azure SQL.
    Stores schema both in memory and in a local JSON file for faster startup.
    """

    CACHE_FILE = "schema_cache.json"

    def __init__(self):
        # cache structure: {table_name: [col1, col2, ...]}
        self.cache: Dict[str, List[str]] = {}

    def _connect(self):
        """Create and return a new SQL connection."""
        try:
            conn = pyodbc.connect(settings.sql_connection_string)
            
            print("[OK]Connected to Azure SQL Database.")
            return conn
        except Exception as e:
            msg = (
                f"\n[ERROR] Could not connect to Azure SQL: {e}\n"
                "Please check the following:\n"
                "  - The connection string in your .env file is correct.\n"
                "  - The ODBC driver specified (e.g. ODBC Driver 18 for SQL Server) is installed.\n"
                "  - Network connectivity and firewall settings allow access to the server.\n"
            )
            raise ConnectionError(msg) from e

    def load_schema(self, force_reload: bool = False) -> Dict[str, List[str]]:
        """
        Load schema (tables and columns) from Azure SQL.
        Uses local JSON cache if available, unless force_reload=True.
        """
        # 1️⃣ Try to load from memory
        if self.cache and not force_reload:
            return self.cache

        # 2️⃣ Try to load from JSON cache
        if not force_reload and os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                print(f"[OK] Loaded schema from cache file ({self.CACHE_FILE})")
                return self.cache
            except Exception as e:
                print(f"[ERROR] Failed to load schema from cache file: {e}")

        # 3️⃣ Fallback: fetch from database
        query = """
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """

        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"[ERROR] Failed to load schema from database: {e}") from e

        # 4️⃣ Build schema dict
        schema: Dict[str, List[str]] = {}
        for table_name, column_name in rows:
            schema.setdefault(table_name, []).append(column_name)

        self.cache = schema

        # 5️⃣ Save to JSON file
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2)
            print(f" Schema cached to {self.CACHE_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to write schema cache file: {e}")

        print(f" Schema loaded: {len(schema)} tables found.")
        return schema

    def get_schema(self) -> Dict[str, List[str]]:
        """Return cached schema (load it if not available)."""
        if not self.cache:
            return self.load_schema()
        return self.cache

    def get_tables(self) -> List[str]:
        """Return a list of table names in the schema."""
        return list(self.cache.keys())

    def get_columns(self, table_name: str) -> List[str]:
        """Return the list of columns for a given table."""
        return self.cache.get(table_name, [])
