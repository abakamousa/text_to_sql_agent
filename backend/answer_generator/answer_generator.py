from backend.services.openai_client import OpenAIClient
import logging

def generate_answer(nl_query: str, sql_query: str, sql_results: str) -> str:
    """
    Use the LLM to generate a natural language summary or answer
    based on the SQL query results.
    """
    client = OpenAIClient()
    llm = client.get_llm()

    prompt = f"""
    You are a helpful data analyst assistant.

    The user asked:
    "{nl_query}"

    The following SQL query was executed:
    {sql_query}

    These are the results (in JSON format):
    {sql_results}

    Write a clear, human-readable answer that summarizes or interprets
    the data meaningfully for a non-technical audience.
    """
    logging.info(f"🧠 Generating answer from LLM. with {nl_query}, {sql_query}, {sql_results}")
    response = llm.invoke(prompt)
    return getattr(response, "content", str(response))
