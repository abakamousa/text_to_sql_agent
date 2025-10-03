from langchain.agents import initialize_agent, AgentType
from services.openai_client import OpenAIClient
from orchestrator.tools import run_sql_tool, guardrails_tool, regenerator_tool

def build_agent():
    """Build and return a LangChain agent with custom tools."""
    llm = OpenAIClient().get_llm()

    tools = [run_sql_tool, guardrails_tool, regenerator_tool]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )
    return agent

def run_agent(nl_query: str) -> dict:
    """Execute a natural language query through the agent."""
    agent = build_agent()
    return {"result": agent.run(nl_query)}
