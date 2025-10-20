from typing import Dict, List
import pyodbc
import json
import os
from backend.models.settings import settings

class SchemaCache:
    """
    Schema cache that stores table/column info including schema names and descriptions.
    """

    CACHE_FILE = "schema_cache.json"

    def __init__(self):
        # Structure: { "schema.table": {"columns": [...], "description": "..." } }
        self.cache: Dict[str, Dict] = {}

    def _connect(self):
        """Create a new SQL connection."""
        try:
            conn = pyodbc.connect(settings.sql_connection_string)
            print("[OK] Connected to Azure SQL Database.")
            return conn
        except Exception as e:
            msg = (
                f"[ERROR] Could not connect to Azure SQL: {e}\n"
                "Check connection string, ODBC driver, and network/firewall settings."
            )
            raise ConnectionError(msg) from e

    def load_schema(self, force_reload: bool = False) -> Dict[str, Dict]:
        """
        Load schema from database or JSON cache.
        Stores fully qualified table names and optional table descriptions.
        """
        if self.cache and not force_reload:
            return self.cache

        # Load from JSON cache if exists
        if not force_reload and os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                print(f"[OK] Loaded schema from cache file ({self.CACHE_FILE})")
                return self.cache
            except Exception as e:
                print(f"[ERROR] Failed to load JSON cache: {e}")

        # Fetch from database
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            COLUMN_NAME,
            CAST(ISNULL(ep.value, '') AS NVARCHAR(MAX)) AS TABLE_DESCRIPTION
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN sys.tables t ON t.name = c.TABLE_NAME
        LEFT JOIN sys.extended_properties ep
            ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """

        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"[ERROR] Failed to load schema from database: {e}") from e

        # Build cache
        schema: Dict[str, Dict] = {}
        for schema_name, table_name, column_name, table_desc in rows:
            fq_table = f"{schema_name}.{table_name}"
            if fq_table not in schema:
                schema[fq_table] = {"columns": [], "description": table_desc or "No description available."}
            schema[fq_table]["columns"].append(column_name)

        self.cache = schema

        # Save to JSON
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            print(f"[OK] Schema cached to {self.CACHE_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to write schema cache file: {e}")

        print(f"[OK] Loaded schema: {len(schema)} tables")
        return schema

    def get_schema(self) -> Dict[str, Dict]:
        if not self.cache:
            return self.load_schema()
        return self.cache

    def get_tables(self) -> List[str]:
        return list(self.cache.keys())

    def get_columns(self, fq_table_name: str) -> List[str]:
        return self.cache.get(fq_table_name, {}).get("columns", [])

    def get_table_description(self, fq_table_name: str) -> str:
        return self.cache.get(fq_table_name, {}).get("description", "No description available.")
