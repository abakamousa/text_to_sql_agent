import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv
from models.api_models import SQLQueryRequest, SQLQueryResponse
from pydantic import ValidationError

# Load .env
load_dotenv()

API_URL = os.getenv("FUNCTION_API_URL", "http://localhost:7071/api/query")

st.set_page_config(page_title="Text-to-SQL Agent", layout="wide")
st.title("🧑‍💻 Text-to-SQL Agent on Azure")
st.write("Enter a natural language query and let the agent generate SQL and results.")

# Input form
with st.form("query_form"):
    nl_query = st.text_area("Your question:", height=120, placeholder="e.g. Show me the 10 most recent orders")
    submitted = st.form_submit_button("Run Query")

if submitted and nl_query.strip():
    try:
        # Validate request with Pydantic
        payload = SQLQueryRequest(query=nl_query).dict()

        with st.spinner("🔎 Thinking..."):
            response = requests.post(API_URL, json=payload, timeout=60)

        if response.status_code == 200:
            try:
                data = SQLQueryResponse.parse_raw(response.text)

                # Show SQL
                st.subheader("📝 Generated SQL")
                st.code(data.result, language="sql")

                # Show results if present
                if data.rows:
                    df = pd.DataFrame(data.rows)
                    st.subheader("📊 Query Results")
                    st.dataframe(df, use_container_width=True)
                    if data.row_count is None:
                        st.caption(f"Rows returned: {len(df)}")
                    else:
                        st.caption(f"Rows returned: {data.row_count}")
                else:
                    st.info("No rows returned from the database.")

                # Show execution time if available
                if data.execution_time:
                    st.caption(f"Query executed in {data.execution_time:.2f}s")

            except ValidationError as ve:
                st.error(f"Invalid response format: {ve}")

        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")

    except ValidationError as ve:
        st.error(f"Invalid request: {ve}")
    except Exception as e:
        st.error(f"🚨 Failed to reach API: {str(e)}")
