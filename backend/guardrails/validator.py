import yaml
import logging
from pathlib import Path
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class Guardrails:
    """
    Encapsulates SQL validation rules for safety and governance.
    Loads rules from a YAML file (e.g., blocked keywords, allowed tables).
    """

    def __init__(self, rules_path: str | None = None):
        default_path = Path(__file__).parent / "rules.yaml"
        self.rules_path = Path(rules_path) if rules_path else default_path

        # Load rules from YAML
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f) or {}
            logger.info(f"Loaded guardrail rules from {self.rules_path}")
        except Exception as e:
            logger.warning(f"Failed to load guardrail rules: {e}. Using defaults.")
            rules = {}

        """ self.blocked_keywords: List[str] = [
            kw.strip().upper() for kw in rules.get("blocked_keywords", [])
        ]"""

        blocked_keywords_raw = rules.get("blocked_keywords") or []
        self.blocked_keywords = [
            kw.strip().upper() for kw in blocked_keywords_raw if isinstance(kw, str)
        ]
        allowed_tables_raw = rules.get("allowed_tables") or []
        self.allowed_tables: List[str] = [
            tbl.strip().upper() for tbl in allowed_tables_raw if isinstance(tbl, str)
        ]

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def validate(self, sql: str) -> Dict[str, Any]:
        """
        Validate a SQL query against defined guardrails.

        Returns:
            dict: {
                "ok": bool,
                "errors": list[str]
            }
        """
        errors: List[str] = []

        if not sql or not sql.strip():
            return {"ok": False, "errors": ["Empty SQL statement."]}

        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return {"ok": False, "errors": ["SQL could not be parsed."]}
        except Exception as e:
            return {"ok": False, "errors": [f"SQL parsing error: {e}"]}

        # --- 1) Blocked keyword detection (token-level) ---
        for kw in self.blocked_keywords:
            # check token-wise instead of substring to avoid false positives
            found = False
            for stmt in parsed:
                for token in stmt.flatten():
                    if isinstance(token.value, str) and token.value.strip().upper() == kw:
                        found = True
                        break
                if found:
                    break
            if found:
                errors.append(f"Blocked keyword detected: {kw}")

        # --- 2) Allowed table enforcement (uses parsed table names) ---
        if self.allowed_tables:
            used_tables = self._extract_table_names(parsed)
            # Normalize and compare fully-qualified or simple names
            unauthorized = []
            for t in used_tables:
                if not t:
                    continue
                # compare both simple name and fully qualified
                t_upper = t.upper()
                simple_name = t_upper.split(".")[-1]
                if t_upper not in self.allowed_tables and simple_name not in self.allowed_tables:
                    unauthorized.append(t)
            if unauthorized:
                errors.append(f"Unauthorized tables detected: {', '.join(sorted(set(unauthorized)))}")

        # --- 3) Basic sanity check for DML presence ---
        has_dml = any(
            token.ttype is DML and token.value.upper() in {"SELECT", "UPDATE", "INSERT", "DELETE"}
            for stmt in parsed
            for token in stmt.tokens
        )
        if not has_dml:
            errors.append("Query does not contain a valid DML statement (SELECT, INSERT, UPDATE, DELETE).")

        return {"ok": not errors, "errors": errors}

    # ---------------------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------------------
    def _extract_table_names(self, parsed) -> List[str]:
        """
        Extract table names from parsed SQL statements.
        Returns fully-qualified names where present (schema.table).
        """
        tables = set()

        for stmt in parsed:
            from_seen = False
            for token in stmt.tokens:
                # if we just saw FROM, next identifier(s) are table names
                if from_seen:
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            name = identifier.get_real_name() or identifier.get_name()
                            # try to get schema if present
                            fq = identifier.get_name() or name
                            tables.add(fq)
                        from_seen = False
                    elif isinstance(token, Identifier):
                        name = token.get_real_name() or token.get_name()
                        fq = token.get_name() or name
                        tables.add(fq)
                        from_seen = False
                    elif token.ttype is Keyword:
                        from_seen = False
                    # else: skip other token types until we hit next meaningful token
                if token.ttype is Keyword and token.value.upper() == "FROM":
                    from_seen = True

            # also look for JOIN clauses which reference tables
            for token in stmt.tokens:
                if token.ttype is Keyword and token.value.upper() == "JOIN":
                    # next meaningful token should be an identifier
                    idx = stmt.token_index(token)
                    # safe-guard: iterate following tokens to find identifier
                    for next_tok in stmt.tokens[idx + 1:]:
                        if isinstance(next_tok, Identifier):
                            name = next_tok.get_real_name() or next_tok.get_name()
                            fq = next_tok.get_name() or name
                            tables.add(fq)
                            break
                        if next_tok.ttype is Keyword:
                            break

        # Filter out empty strings and return list
        return [t for t in tables if t]

    # Optional public utility
    def parse_tables(self, sql: str) -> List[str]:
        """Return tables referenced in a SQL query."""
        try:
            parsed = sqlparse.parse(sql)
            return self._extract_table_names(parsed)
        except Exception as e:
            logger.error(f"Failed to parse tables: {e}")
            return []
