from backend.sql_executor.executor import  SQLExecutor 
from backend.guardrails.validator import Guardrails
from backend.regenerator.fixer import SQLRegenerator

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


def main():
    print("Select a module to run:")
    print("1 - SQL Executor")
    print("2 - Guardrails Validator")
    print("3 - SQL Regenerator")

    choice = input("Enter choice (1/2/3): ").strip()
    if choice == "1":
        run_sql_executor()
    elif choice == "2":
        run_guardrails()
    elif choice == "3":
        run_regenerator()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
