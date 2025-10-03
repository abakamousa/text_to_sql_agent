# Demo text to Sql application

Lightweight demo that converts natural-language queries into SQL, validates them with guardrails, executes against Azure SQL, and can regenerate/fix failing statements using an LLM.


# Architecture

<img width="1664" height="672" alt="text_to_agent_archi drawio" src="https://github.com/user-attachments/assets/adf036c4-2846-4201-a675-f3da0b83e255" />

# Quick overview of components
- Azure Function API: [backend/function_app.py](backend/function_app.py) exposing the HTTP endpoint implemented by the `query_agent` function ([`function_app.query_agent`](backend/function_app.py)).
- Orchestrator / Agent: Agent construction and run entry point in [backend/orchestrator/agent.py](backend/orchestrator/agent.py) — see [`orchestrator.agent.run_agent`](backend/orchestrator/agent.py).
- Tools used by the agent: [backend/orchestrator/tools.py](backend/orchestrator/tools.py) — includes [`orchestrator.tools.run_sql_tool`](backend/orchestrator/tools.py), [`orchestrator.tools.guardrails_tool`](backend/orchestrator/tools.py), and [`orchestrator.tools.regenerator_tool`](backend/orchestrator/tools.py).
- Chains & prompts: Prompt templates and chain builders in [backend/orchestrator/chains.py](backend/orchestrator/chains.py) — see [`orchestrator.chains.get_sql_generation_chain`](backend/orchestrator/chains.py) and [`orchestrator.chains.get_regeneration_chain`](backend/orchestrator/chains.py). Prompts live under [backend/orchestrator/prompts/](backend/orchestrator/prompts/).
- OpenAI client wrapper: [backend/services/openai_client.py](backend/services/openai_client.py) — [`services.openai_client.OpenAIClient`](backend/services/openai_client.py).
- Guardrails: SQL validation rules loader and validator in [backend/guardrails/guardrails.py](backend/guardrails/guardrails.py) — [`guardrails.Guardrails`](backend/guardrails/guardrails.py). Rules file: [backend/guardrails/rules.yaml](backend/guardrails/rules.yaml).
- SQL execution: low-level executor in [backend/sql_executor/executor.py](backend/sql_executor/executor.py) — see [`sql_executor.executor.SQLExecutor`](backend/sql_executor/executor.py) and convenience [`sql_executor.executor.run_query`](backend/sql_executor/executor.py).
- Schema cache: simple in-memory schema store in [backend/sql_executor/schema_cache.py](backend/sql_executor/schema_cache.py) — [`sql_executor.schema_cache.SchemaCache`](backend/sql_executor/schema_cache.py). (Note: the project shows calls to `load_schema` / `get_schema` in some places; extend `SchemaCache` if you need those helpers.)
- SQL regenerator: repair/fix logic for failing SQL in [backend/regenerator/fixer.py](backend/regenerator/fixer.py) — [`regenerator.fixer.SQLRegenerator`](backend/regenerator/fixer.py).
- Frontend: Streamlit demo at [frontend/streamlit_app.py](frontend/streamlit_app.py). Request/response models are in [frontend/models/api_models.py](frontend/models/api_models.py) — [`frontend.models.api_models.SQLQueryRequest`](frontend/models/api_models.py) and [`frontend.models.api_models.SQLQueryResponse`](frontend/models/api_models.py).

# Prerequisites
- Python >= 3.11
- Azure Functions Core Tools (if running the Azure Function locally)
- ODBC Driver for SQL Server (for pyodbc)
- An Azure OpenAI deployment configured (or local LLM) and a reachable Azure SQL instance

# Install dependencies
1. Create & activate a virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

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
# from repo root
func start
```
The function app code is at [backend/function_app.py](backend/function_app.py).

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


# Notes, limitations & extension points
- Schema caching: current [`sql_executor.schema_cache.SchemaCache`](backend/sql_executor/schema_cache.py) is minimal — extend with `load_schema` / `get_schema` helpers if you rely on them (the orchestrator expects such helpers in some places).
- Guardrails are rule-based via [backend/guardrails/rules.yaml](backend/guardrails/rules.yaml). Customize allowed/blocked lists.
- Chains & prompts are in [backend/orchestrator/chains.py](backend/orchestrator/chains.py) and [backend/orchestrator/prompts/](backend/orchestrator/prompts/). Tweak prompts to change SQL generation/regeneration behavior.
- LLM configuration: [`services.openai_client.OpenAIClient`](backend/services/openai_client.py) wraps Azure Chat OpenAI via LangChain.

# Files of interest
- [pyproject.toml](pyproject.toml)
- [backend/function_app.py](backend/function_app.py)
- [backend/orchestrator/agent.py](backend/orchestrator/agent.py) — [`orchestrator.agent.run_agent`](backend/orchestrator/agent.py)
- [backend/orchestrator/tools.py](backend/orchestrator/tools.py)
- [backend/orchestrator/chains.py](backend/orchestrator/chains.py)
- [backend/services/openai_client.py](backend/services/openai_client.py) — [`services.openai_client.OpenAIClient`](backend/services/openai_client.py)
- [backend/sql_executor/executor.py](backend/sql_executor/executor.py) — [`sql_executor.executor.run_query`](backend/sql_executor/executor.py)
- [backend/regenerator/fixer.py](backend/regenerator/fixer.py) — [`regenerator.fixer.SQLRegenerator`](backend/regenerator/fixer.py)
- [backend/guardrails/guardrails.py](backend/guardrails/guardrails.py) — [`guardrails.Guardrails`](backend/guardrails/guardrails.py)
- [frontend/streamlit_app.py](frontend/streamlit_app.py) and [frontend/models/api_models.py](frontend/models/api_models.py)
