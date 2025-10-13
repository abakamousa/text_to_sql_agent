import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv
from models.api_models import SQLQueryRequest, SQLQueryResponse
from pydantic import ValidationError
from decimal import Decimal

# Load environment variables
load_dotenv()
API_URL = os.getenv("FUNCTION_API_URL", "http://localhost:7071/api/query")

# Streamlit page setup
st.set_page_config(page_title="🧠 Text-to-SQL Agent", layout="wide")
st.title("🧑‍💻 Text-to-SQL Agent on Azure")
st.write("Ask a question in natural language — the agent will generate, validate, and execute SQL, then summarize the results.")

# Input form
with st.form("query_form"):
    nl_query = st.text_area("💬 Your question:", height=120, placeholder="e.g. Show me the 10 most recent orders")
    submitted = st.form_submit_button("🚀 Run Query")

def convert_decimals(obj):
    """Recursively convert Decimal values to float for display."""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

if submitted and nl_query.strip():
    try:
        # Validate and send request
        payload = SQLQueryRequest(query=nl_query).model_dump()

        with st.spinner("🤖 The agent is thinking..."):
            response = requests.post(API_URL, json=payload, timeout=90)

        if response.status_code == 200:
            try:
                data: SQLQueryResponse = SQLQueryResponse.parse_raw(response.text)
                st.success("✅ Query processed successfully!")

                # --- SQL Query Section ---
                st.subheader("🧩 Generated SQL Query")
                if data.sql_query:
                    st.code(data.sql_query, language="sql")
                else:
                    st.info("No SQL query was generated.")

                # --- Validation Section ---
                if data.validation:
                    st.caption(f"Validation: **{data.validation}**")
                if data.regenerations_used is not None:
                    st.caption(f"Regenerations used: {data.regenerations_used}")

                # --- Data Section ---
                st.subheader("📊 SQL Query Results")
                if data.data:
                    df_data = convert_decimals(data.data)
                    try:
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"Rows returned: {len(df)}")
                    except Exception:
                        st.json(df_data)
                else:
                    st.info("No data was returned from the SQL query.")

                # --- LLM Answer Section ---
                st.subheader("🗣️ LLM-Generated Answer")
                if data.answer:
                    st.markdown(f"**Answer:** {data.answer}")
                else:
                    st.info("No answer was generated from the data.")

                # --- Execution Metadata ---
                if data.execution_time:
                    st.caption(f"Execution time: {data.execution_time:.2f}s")

            except ValidationError as ve:
                st.error(f"Invalid response format: {ve}")

        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")

    except ValidationError as ve:
        st.error(f"Invalid request: {ve}")
    except requests.exceptions.Timeout:
        st.error("⏳ The request timed out. Try again or check your API.")
    except Exception as e:
        st.error(f"🚨 Failed to reach API: {str(e)}")
