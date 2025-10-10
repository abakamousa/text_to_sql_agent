from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from backend.services.openai_client import OpenAIClient
from backend.orchestrator.toolset import (
    sql_generator,
    run_sql_tool,
    guardrails_tool,
    regenerator_tool,
)

import logging

logger = logging.getLogger(__name__)

def build_agent():
    """Build and return a ReAct-style SQL agent with memory and tools."""

    # Initialize LLM (Azure OpenAI client)
    service = OpenAIClient()
    llm = service.get_llm()

    # Define available tools
    available_tools = [
        sql_generator,
        run_sql_tool,
        guardrails_tool,
        regenerator_tool,
    ]

    # 🧠 Conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        output_key="output",
        return_messages=True,
    )

    # 🧩 Agent prompt with proper structure
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an expert SQL assistant. You can generate, validate, and execute SQL queries "
                "using the tools provided.\n"
                "Make sure all SQL statements are valid before execution. "
                "If validation fails, use 'regenerator_tool' to correct it."
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # ✅ Create the new tool-aware agent (no manual scratchpad formatting needed)
    agent = create_tool_calling_agent(llm=llm, tools=available_tools, prompt=prompt)

    # ✅ Wrap in an AgentExecutor with memory and verbose logging
    agent_executor = AgentExecutor(
        agent=agent,
        tools=available_tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )

    return agent_executor


def run_agent(nl_query: str, chat_history=None) -> dict:
    """
    Execute a natural language query through the ReAct SQL agent.
    Supports chat memory for multi-turn interactions.
    """
    try:
        agent = build_agent()

        payload = {
            "input": nl_query,
            "chat_history": chat_history or [],
        }

        result = agent.invoke(payload)

        # Safely convert chat memory messages to serializable form
        memory_messages = []
        for msg in agent.memory.chat_memory.messages:
            memory_messages.append({
                "type": msg.__class__.__name__,
                "content": getattr(msg, "content", None)
            })

        return {
            "result": result.get("output", str(result)),
            "memory": memory_messages
        }

    except Exception as e:
        logger.exception(f"Agent execution failed: {e}")
        return {"error": str(e)}
