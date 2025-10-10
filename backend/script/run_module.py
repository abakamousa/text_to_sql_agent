import os
import sys

# Ensure the repository root (two directories up) is added to sys.path.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.sql_executor.executor import  SQLExecutor 
from backend.guardrails.validator import Guardrails
from backend.regenerator.fixer import SQLRegenerator
from backend.sql_executor.schema_cache import SchemaCache
from backend.models.settings import settings
from dotenv import load_dotenv
import pyodbc

load_dotenv()  # Load environment variables from .env file

def run_sql_executor():
    sql = input("Enter SQL to execute: ")
    executor = SQLExecutor()
    result = executor.run_query(sql)
    print("\nResult:")
    print(f"SQL: {result['sql']}")
    print(f"Row count: {result['row_count']}")
    for row in result['rows']:
        print(row)
    print(f"Execution time: {result['execution_time']:.2f}s\n")

def run_schema_cache():
    cache = SchemaCache()
    try:
        cache.load_schema()
        schema = cache.get_schema()
        print("\nCached Schema:")
        for table, columns in schema.items():
            print(f"{table}: {', '.join(columns)}")
        print()
    except RuntimeError as e:
        print(f"Error loading schema: {e}\n")

def run_guardrails():
    sql = input("Enter SQL to validate: ")
    guard = Guardrails()
    result = guard.validate(sql)
    print("\nValidation Result:")
    print(result, "\n")


def run_regenerator():
    nl_query = input("Enter natural language query: ")
    bad_sql = input("Enter bad SQL: ")
    errors = input("Enter validation errors: ")

    regenerator = SQLRegenerator()
    fixed_sql = regenerator.regenerate(nl_query, bad_sql, errors)
    print("\nRegenerated SQL:")
    print(fixed_sql, "\n")

def test_connection():
    print("Using connection string from .env:")
    print(settings.sql_connection_string)
    try:
        conn = pyodbc.connect(settings.sql_connection_string)
        print("✅ Connected successfully to Azure SQL Database!")
        conn.close()
    except Exception as e:
        print("❌ Error connecting to database:")
        print(e)


def main():
    print("Select a module to run:")
    print("1 - SQL Executor")
    print("2 - Guardrails Validator")
    print("3 - SQL Regenerator")
    print("4 - Schema Cache Loader")
    print("5 - test connection to database")

    choice = input("Enter choice (1/2/3/4/5): ").strip()
    if choice == "1":
        run_sql_executor()
    elif choice == "2":
        run_guardrails()
    elif choice == "3":
        run_regenerator()
    elif choice == "4":
        run_schema_cache()
    elif choice == "5":
        test_connection()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
