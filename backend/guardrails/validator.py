import yaml
from pathlib import Path
from sqlparse import parse

class Guardrails:
    """
    Encapsulates SQL guardrail logic.
    Loads rules from a YAML file.
    """

    def __init__(self, rules_path: str | None = None):
        rules_path = rules_path or Path(__file__).parent / "rules.yaml"

        with open(rules_path, "r") as f:
            rules = yaml.safe_load(f)

        self.blocked_keywords = rules.get("blocked_keywords", [])
        self.allowed_tables = rules.get("allowed_tables", [])

    def validate(self, sql: str) -> dict:
        """
        Validate a SQL query.

        Returns:
            dict: {
                "ok": bool,
                "errors": List[str]
            }
        """
        errors = []

        sql_upper = sql.upper()

        # Check blocked keywords
        for kw in self.blocked_keywords:
            if kw.upper() in sql_upper:
                errors.append(f"Blocked keyword detected: {kw}")

        # Check allowed tables
        if self.allowed_tables:
            if not any(table.upper() in sql_upper for table in self.allowed_tables):
                errors.append("Unauthorized table used.")

        return {"ok": not errors, "errors": errors}

    def parse_tables(self, sql: str) -> list[str]:
        """
        Optional helper: returns a list of tables referenced in the SQL.
        """
        parsed = parse(sql)
        tables = set()
        for stmt in parsed:
            for token in stmt.tokens:
                if token.ttype is None and "." not in token.value:
                    # crude heuristic
                    tables.add(token.value)
        return list(tables)
