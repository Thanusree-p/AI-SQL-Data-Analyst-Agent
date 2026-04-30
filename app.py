import streamlit as st
import pandas as pd
import sqlite3
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import plotly.express as px

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="AI SQL Data Analyst", layout="wide")
st.title("📊 AI SQL Data Analyst Agent")

# ---------------- LOAD API ---------------- #
load_dotenv()

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

# ---------------- CLEAN CODE ---------------- #
def clean_code(code):
    code = re.sub(r"```sql", "", code)
    code = code.replace("```", "")
    return code.strip()

# ---------------- SAFE SQL CHECK ---------------- #
def is_safe_query(query):
    unsafe_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
    return not any(word in query.upper() for word in unsafe_keywords)

# ---------------- FILE UPLOAD ---------------- #
file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)

    st.subheader("📄 Data Preview")
    st.dataframe(df.head())

    # Create SQLite DB
    conn = sqlite3.connect("data.db")
    df.to_sql("data", conn, if_exists="replace", index=False)

    question = st.text_input("Ask a question about your data")

    if question:

        # ---------------- PROMPT (IMPROVED) ---------------- #
        prompt = f"""
You are a senior data analyst.

Table name: data
Columns: {list(df.columns)}

Convert the following question into a valid SQLite SQL query.

STRICT RULES:
- Only return SQL query
- Do NOT explain anything
- Use correct column names exactly
- Use LIMIT when needed
- Avoid unsafe operations (DROP, DELETE, etc.)

Question: {question}
"""

        response = llm.invoke(prompt)
        sql_query = clean_code(response.content)

        st.subheader("🧠 Generated SQL")
        st.code(sql_query, language="sql")

        # ---------------- SAFETY CHECK ---------------- #
        if not is_safe_query(sql_query):
            st.error("❌ Unsafe query detected!")
        else:
            try:
                result = pd.read_sql_query(sql_query, conn)

                st.subheader("📊 Result")
                st.dataframe(result)

                # ---------------- SMART VISUALIZATION ---------------- #
                if len(result) > 1 and len(result.columns) >= 2:
                    fig = px.bar(result, x=result.columns[0], y=result.columns[1])
                    st.plotly_chart(fig)

                elif len(result) == 1 and len(result.columns) == 2:
                    chart_df = result.T.reset_index()
                    chart_df.columns = ["Category", "Value"]

                    fig = px.bar(chart_df, x="Category", y="Value")
                    st.plotly_chart(fig)

                else:
                    st.info("No suitable data for visualization")

            except Exception as e:
                st.error(f"Execution Error: {e}")