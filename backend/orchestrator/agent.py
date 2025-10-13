import logging
import json
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from backend.services.openai_client import OpenAIClient
from backend.utils.logger import log_with_task
#from backend.visualization.visualisation_recommander import recommend_visualizations
from backend.orchestrator.toolset import (
    sql_generator,
    run_sql_tool,
    guardrails_tool,
    regenerator_tool,
    visualization_tool,
    answer_generator_tool,
)

logger = logging.getLogger(__name__)
MAX_REGENERATIONS = 2  # Control number of invalid SQL regenerations
PROJECT_TASK = "SQL-Agent"

from decimal import Decimal

def convert_decimals(obj):
    """Recursively convert Decimal to float in dict/list structures."""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
    

def get_tool_by_name(agent, name: str):
    """Helper to fetch a tool object by its name."""
    for tool in agent.tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found among: {[t.name for t in agent.tools]}")

def build_agent():
    """Build a ReAct-style SQL agent with memory and tools."""
    service = OpenAIClient()
    llm = service.get_llm()

    available_tools = [
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
                "You are an expert SQL and data visualization agent. You generate SQL queries, validate them, execute them, summarize results, "
                "and recommend visualizations. Always ensure SQL safety and interpretability."
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=available_tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=available_tools,
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
        #payload = {"input": nl_query, "chat_history": chat_history or []}

        # Fetch tools
        sql_gen_tool = get_tool_by_name(agent, "sql_generator")
        guard_tool = get_tool_by_name(agent, "guardrails_tool")
        regen_tool = get_tool_by_name(agent, "regenerator_tool")
        run_sql = get_tool_by_name(agent, "run_sql_tool")
        viz_tool = get_tool_by_name(agent, "visualization_tool")
        answer_tool = get_tool_by_name(agent, "answer_generator_tool")
        log_with_task(logging.INFO, f"Tools loaded successfully ", task="Tools-loading")

        # Step 1: Generate SQL
        sql_query = sql_gen_tool.func(nl_query)
        log_with_task(logging.INFO, f"Generated SQL: {sql_query}", task="SQL-Generation")

        # Step 2: Validate & Regenerate if necessary
        validation_result = guard_tool.func(sql_query)
        regenerations = 0
        log_with_task(logging.INFO, f"Validation of the generated SQL request with guardrail validator", task="SQL-Validation")

        while validation_result != "VALID" and regenerations < MAX_REGENERATIONS:
            log_with_task(logging.WARNING, f"SQL invalid. Regenerating (attempt {regenerations + 1})...", task="SQL-Validation")
            regen_input = {
                "nl_query": nl_query,
                "bad_sql": sql_query,
                "errors": validation_result
            }
            sql_query = regen_tool.func(json.dumps(regen_input))
            validation_result = guard_tool.func(sql_query)
            regenerations += 1

        if validation_result != "VALID":
            log_with_task(logging.ERROR, "SQL could not be validated after multiple attempts.", task="SQL-Validation")
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
            data = query_result.get("rows", [])
            execution_time = query_result.get("execution_time")
        except Exception as e:
            log_with_task(logging.ERROR, f"SQL execution failed: {e}", task="SQL-Execution")
            return {
                "sql_query": sql_query,
                "validation": "VALID",
                "error": str(e),
                "regenerations_used": regenerations,
            }

        data = convert_decimals(query_result.get("rows", [])) 
        if not data:
            log_with_task(logging.INFO, "No data returned from SQL query.", task="SQL-Execution")
            return {
                "sql_query": sql_query,
                "validation": "VALID",
                "data": [],
                "answer": "No data returned from the database.",
                "regenerations_used": regenerations,
                "execution_time": execution_time
            }

        log_with_task(logging.INFO, f"SQL executed successfully. Rows returned: {len(data)}", task="SQL-Execution")
        # Step 4: Generate LLM answer using retrieved data
        
        answer_input = {
            "query": nl_query,
            "sql": sql_query or "No SQL generated",
            "data": data or [{"info": "No rows returned"}],
        }
        #logging.info(f"Generating answer with data: {answer_input}")
        answer = answer_tool.func(json.dumps(answer_input))
        log_with_task(logging.INFO, "SQL query executed and answer generated successfully.", task="Agent-Finish")
        
    
        # Step 5: Recommend Visualization
        viz_input = {
            "nl_query": nl_query,
            "sql_query": sql_query,
            "data": data or [{"info": "No rows returned"}],
        }       
        viz_recommendation = viz_tool.func(json.dumps(viz_input))
        log_with_task(logging.INFO, "Visualization recommended successfully.", task="Visualization-Recommendation") 
        return {
            "sql_query": sql_query,
            "validation": "VALID",
            "data": data,
            "answer": answer,
            "visualization": viz_recommendation,
            "regenerations_used": regenerations,
            "execution_time": execution_time
        }   


    except Exception as e:
        log_with_task(logging.ERROR, f"Agent execution failed: {e}", task="Agent-Execution")
        return {"error": str(e)}
