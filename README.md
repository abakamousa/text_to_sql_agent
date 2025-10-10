# Demo text to Sql application

Lightweight demo that converts natural-language queries into SQL, validates them with guardrails, executes against Azure SQL, and can regenerate/fix failing statements using an LLM.


# Architecture

<img width="1664" height="672" alt="text_to_agent_archi drawio" src="https://github.com/user-attachments/assets/adf036c4-2846-4201-a675-f3da0b83e255" />

## 🚀 Features

✅ Converts **natural language queries → SQL statements**  
✅ Validates SQL using **custom guardrails**  
✅ Executes against **Azure SQL database**  
✅ Automatically **regenerates/fixes invalid SQL**  
✅ Built with **LangChain ReAct** agent pattern  
✅ Supports **conversation memory** for multi-turn queries  
✅ Deployed as an **Azure Function API**


## 🧠 How It Works

The agent follows a controlled ReAct reasoning loop using LangChain’s AgentExecutor.

- User Input:
“Show me the total sales per region in 2024.”

- Step 1 – Generate SQL
Uses sql_generator tool → produces SQL query.

- Step 2 – Validate SQL
Uses guardrails_tool → ensures correctness and safety.

- Step 3 – Execute SQL
Uses run_sql_tool → runs against Azure SQL and returns results.

- Step 4 – Regenerate if needed
If validation fails, uses regenerator_tool up to N times (max_regenerations).

# Prerequisites
- Python >= 3.11
- Azure Functions Core Tools (if running the Azure Function locally)
- ODBC Driver for SQL Server (for pyodbc)
- An Azure OpenAI deployment configured (or local LLM) and a reachable Azure SQL instance

# Install dependencies
1. Create a virtual environment:
```bash
uv  venv 
```
2. Activate the virtual environment:
```bash
# Windows (PowerShell):
.\venv\Scripts\Activate
```

3. Install required dependencies using uv:
```bash
uv sync
```

This will automatically install all the dependencies from pyproject.toml

2. Install from the pyproject dependencies:
```bash
python -m pip install --upgrade pip
python -m pip install .
```

# Configuration (.env)
## frontend
- Copy the example files and update:
  - Root env: [.env.example](.env.example) -> .env
  - Frontend env: [frontend/.env.example](frontend/.env.example) -> frontend/.env
- Key env vars:
  - AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION — used by [`services.openai_client.OpenAIClient`](backend/services/openai_client.py).
  - SQL_CONNECTION_STRING — used by [`sql_executor.executor.SQLExecutor`](backend/sql_executor/executor.py).
  - APPINSIGHTS_KEY, ENVIRONMENT — optional monitoring/settings in [`models.settings.settings`](backend/models/settings.py).

## backend
- Copy the example files and update:
  - Root env: [.env.example](.env.example) -> .env
  - Frontend env: [frontend/.env.example](frontend/.env.example) -> frontend/.env
- Key env vars:
  - AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION — used by [`services.openai_client.OpenAIClient`](backend/services/openai_client.py).
  - SQL_CONNECTION_STRING — used by [`sql_executor.executor.SQLExecutor`](backend/sql_executor/executor.py).
  - APPINSIGHTS_KEY, ENVIRONMENT — optional monitoring/settings in [`models.settings.settings`](backend/models/settings.py).

# Run locally (development)
- Streamlit UI:
```bash
streamlit run frontend/streamlit_app.py
```
This UI posts JSON to the configured FUNCTION_API_URL (see [frontend/.env](frontend/.env)).


- CLI demo script (simple local runner):
```bash
python backend/script/run_module.py
```
This script exercises SQL execution, guardrails validation and regeneration flows interactively.

- Run Azure Function locally (requires Azure Functions Core Tools):
```bash
# cd  backend/azure_function
func start
```
The function app code is at [backend/azure_function/function_app.py](backend/azure_function/function_app.py).

API contract
- Request model: see [`frontend.models.api_models.SQLQueryRequest`](frontend/models/api_models.py).
- Response model: see [`frontend.models.api_models.SQLQueryResponse`](frontend/models/api_models.py).
- The function expects a POST JSON body: { "query": "..." } and returns agent results produced by [`orchestrator.agent.run_agent`](backend/orchestrator/agent.py).

Testing & CI
- Tests folders: [backend/tests](backend/tests) and [frontend/tests](frontend/tests).
- CI workflows: [.github/workflows/backend.yml](.github/workflows/backend.yml) and [.github/workflows/frontend.yml](.github/workflows/frontend.yml).
- Run tests:
```bash
python -m pytest
```



# 📜 License

MIT License © 2025 — Developed by Moussa Aboubakar
