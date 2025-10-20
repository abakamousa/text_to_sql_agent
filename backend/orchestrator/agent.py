import logging
import json
import sys
from decimal import Decimal
from pathlib import Path


# Dynamically add project root (two levels up from current file)
CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[2]  # Points to text_to_sql_agent/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- LangChain Imports ---
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

# --- Internal Imports ---
from backend.services.openai_client import OpenAIClient
from backend.utils.logger import log_with_task
from backend.orchestrator.toolset import (
    sql_generator,
    run_sql_tool,
    guardrails_tool,
    regenerator_tool,
    visualization_tool,
    answer_generator_tool,
)

logger = logging.getLogger(__name__)
MAX_REGENERATIONS = 2
PROJECT_TASK = "SQL-Agent"


# =====================================
# 🧹 Utility
# =====================================
def convert_decimals(obj):
    """Recursively convert Decimal to float for JSON serialization."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def get_tool_by_name(agent, name: str):
    """Fetch a specific tool by its name from the agent."""
    for tool in agent.tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found among: {[t.name for t in agent.tools]}")


# =====================================
# 🧠 Agent Construction
# =====================================
def build_agent():
    """Build the SQL + Visualization LLM agent."""
    service = OpenAIClient()
    llm = service.get_llm()

    tools = [
        sql_generator,
        guardrails_tool,
        regenerator_tool,
        run_sql_tool,
        visualization_tool,
        answer_generator_tool,
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        output_key="output",
        return_messages=True,
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an expert SQL and data visualization agent. "
                "You generate SQL queries, validate them, execute them, summarize results, "
                "and recommend clear visualizations (bar, line, scatter, pie, etc.) based on data."
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )


# =====================================
# 🚀 Main Execution
# =====================================
def run_agent(nl_query: str, chat_history=None) -> dict:
    """Execute full pipeline: NL → SQL → Validate → Execute → Answer → Visualization."""
    try:
        agent = build_agent()

        # Fetch tools
        sql_gen_tool = get_tool_by_name(agent, "sql_generator")
        guard_tool = get_tool_by_name(agent, "guardrails_tool")
        regen_tool = get_tool_by_name(agent, "regenerator_tool")
        run_sql = get_tool_by_name(agent, "run_sql_tool")
        viz_tool = get_tool_by_name(agent, "visualization_tool")
        answer_tool = get_tool_by_name(agent, "answer_generator_tool")

        log_with_task(logging.INFO, "Tools loaded successfully", task="Tools-Loading")

        # Step 1: Generate SQL
        sql_query = sql_gen_tool.func(nl_query)
        log_with_task(logging.INFO, f"Generated SQL: {sql_query}", task="SQL-Generation")

        # Step 2: Validate SQL
        validation_result = guard_tool.func(sql_query)
        regenerations = 0
        log_with_task(logging.INFO, "Validating SQL with guardrails", task="SQL-Validation")

        while validation_result != "VALID" and regenerations < MAX_REGENERATIONS:
            log_with_task(logging.WARNING, f"SQL invalid (attempt {regenerations + 1})", task="SQL-Validation")
            regen_input = {"nl_query": nl_query, "bad_sql": sql_query, "errors": validation_result}
            sql_query = regen_tool.func(json.dumps(regen_input))
            validation_result = guard_tool.func(sql_query)
            regenerations += 1

        if validation_result != "VALID":
            log_with_task(logging.ERROR, "SQL validation failed after multiple attempts.", task="SQL-Validation")
            return {
                "sql_query": sql_query,
                "validation": validation_result,
                "error": "SQL could not be validated after multiple attempts.",
                "regenerations_used": regenerations
            }

        # Step 3: Execute SQL
        try:
            log_with_task(logging.INFO, f"Executing SQL query: {sql_query}", task="SQL-Execution")
            query_result = run_sql.func(sql_query)
            data = convert_decimals(query_result.get("rows", []))
            execution_time = query_result.get("execution_time")
        except Exception as e:
            log_with_task(logging.ERROR, f"SQL execution failed: {e}", task="SQL-Execution")
            return {"sql_query": sql_query, "validation": "VALID", "error": str(e)}

        if not data:
            log_with_task(logging.INFO, "No data returned from SQL query.", task="SQL-Execution")
            return {
                "sql_query": sql_query,
                "validation": "VALID",
                "data": [],
                "answer": "No data returned.",
                "execution_time": execution_time
            }

        # Step 4: Generate Answer
        answer_input = {"query": nl_query, "sql": sql_query, "data": data}
        answer = answer_tool.func(json.dumps(answer_input))
        log_with_task(logging.INFO, "Generated LLM answer.", task="Answer-Generation")

        # Step 5: Recommend Visualization
        viz_input = {"nl_query": nl_query, "sql_query": sql_query, "data": data}
        viz_recommendation = viz_tool.func(json.dumps(viz_input))
        log_with_task(logging.INFO, "Visualization recommendation complete.", task="Visualization-Recommendation")

        return {
            "sql_query": sql_query,
            "validation": "VALID",
            "data": data,
            "answer": answer,
            "visualization": viz_recommendation,
            "regenerations_used": regenerations,
            "execution_time": execution_time,
        }

    except Exception as e:
        log_with_task(logging.ERROR, f"Agent execution failed: {e}", task="Agent-Execution")
        return {"error": str(e)}
