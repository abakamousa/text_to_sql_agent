from typing import Dict

class SchemaCache:
    """
    Simple in-memory cache for database table/schema info.
    Can be extended to refresh periodically.
    """
    def __init__(self):
        self.cache: Dict[str, list[str]] = {}

    def get_tables(self, db_name: str) -> list[str] | None:
        return self.cache.get(db_name)

    def set_tables(self, db_name: str, tables: list[str]):
        self.cache[db_name] = tables
