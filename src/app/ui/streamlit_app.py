"""Enhanced Streamlit UI for Multi-Agent Analytics with rich visualization."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.agents.non_data_agent import NonDataQAAgent
from app.agents.router_agent import RouterAgent
from app.agents.sql_planner_agent import SqlPlannerAgent
from app.agents.synthesizer_agent import SynthesizerAgent
from app.db.engine import get_engine
from app.db.schema_introspector import introspect_schema
from app.db.sql_runner import run_sql
from app.graph.builder import build_graph
from app.llm.bedrock_client import BedrockClient
from app.ui.agent_trace_ui import (
    render_agent_trace_panel,
    render_query_result_table,
    render_synthesis_result,
)

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Analytics Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-header">🤖 Multi-Agent Analytics Platform</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Ask questions in natural language and get intelligent insights from your data</div>',
    unsafe_allow_html=True,
)

# Initialize session state for conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Initialize database and schema
@st.cache_resource
def init_services():
    """Initialize database engine and introspect schema."""
    engine = get_engine()
    schema = introspect_schema(engine)
    schema_text = "\n".join(
        f"Table {t.name}: " + ", ".join(f"{c['name']} ({c['type']})" for c in t.columns)
        for t in schema
    )
    return engine, schema, schema_text


engine, schema, schema_text = init_services()

# Initialize LLM and agents
@st.cache_resource
def init_agents():
    """Initialize LLM client and all agents."""
    try:
        llm = BedrockClient()
        router = RouterAgent(llm)
        non_data = NonDataQAAgent(llm)
        synth = SynthesizerAgent(llm)
        return llm, router, non_data, synth, None
    except Exception as e:  # noqa: BLE001
        error_msg = f"Failed to initialize Bedrock: {e}"
        return None, None, None, None, error_msg


llm, router, non_data, synth, init_error = init_agents()


def planner_factory(_schema: str):
    """Factory function to create SQL planner with schema."""
    return SqlPlannerAgent(llm, schema_text)  # type: ignore[arg-type]


def sql_executor(sql: str):
    """Execute SQL and return results."""
    res = run_sql(engine, sql, preview=True)
    return {"columns": res.columns, "rows": res.rows, "row_count": res.row_count}


# Build graph if agents are initialized
if llm and router and non_data and synth:
    app = build_graph(router, planner_factory, non_data, synth, sql_executor)
else:
    app = None

# Sidebar: Schema Browser and Settings
with st.sidebar:
    st.markdown("## ⚙️ Settings & Schema")

    # Status indicator
    if app:
        st.success("✅ System Ready")
    else:
        st.error("❌ System Not Ready")
        if init_error:
            st.error(init_error)
            st.info(
                "Please ensure AWS credentials are configured and Bedrock is accessible."
            )

    st.markdown("---")

    # Schema browser
    st.markdown("### 📚 Database Schema")
    st.caption(f"{len(schema)} table(s) available")

    for table in schema:
        with st.expander(f"📊 {table.name}"):
            df = pd.DataFrame(table.columns)
            st.dataframe(df, hide_index=True)

    st.markdown("---")

    # Clear conversation button
    if st.button("🗑️ Clear Conversation History"):
        st.session_state.conversation_history = []
        st.rerun()

# Main content area
if not app:
    st.warning(
        "⚠️ **System not ready.** Please configure AWS credentials and ensure Bedrock access."
    )
    st.info(
        "This platform uses AWS Bedrock with Nova models. Ensure the following environment "
        "variables are set: `AWS_REGION`, `BEDROCK_LLM_MODEL_ID`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`"
    )
    st.stop()

# Display conversation history
if st.session_state.conversation_history:
    st.markdown("## 💬 Conversation History")
    for idx, entry in enumerate(st.session_state.conversation_history):
        st.markdown(f"### Query {idx + 1}")
        st.info(f"**You:** {entry['question']}")

        # Show brief answer
        answer = entry.get("final_answer")
        if answer:
            st.success(f"**Assistant:** {answer}")

        # Expandable trace details
        with st.expander("🔍 View Detailed Execution Trace"):
            trace = entry.get("trace", {})
            render_agent_trace_panel(trace)

            # Show synthesis if available
            synthesis = trace.get("synthesis_output")
            if synthesis:
                render_synthesis_result(synthesis)

            # Show raw data if available
            result = entry.get("result")
            if result and result.get("columns"):
                render_query_result_table(result)

        st.markdown("---")

# Chat input
st.markdown("## 💭 Ask a Question")

prompt = st.chat_input(
    "Ask anything: 'What are the top 5 products by sales?', 'Show customer trends', 'Hello!', etc."
)

if prompt:
    # Show user message
    with st.chat_message("user"):
        st.write(prompt)

    # Process with spinner
    with st.spinner("🤖 Agents are working on your request..."):
        state = {"user_message": prompt}
        final_state = app.invoke(state)

    # Extract results
    trace = final_state.get("trace", {})
    result = final_state.get("result")
    final_answer = final_state.get("final_answer", "Analysis complete.")

    # Display answer
    with st.chat_message("assistant"):
        st.markdown(f"**{final_answer}**")

    # Show detailed trace
    st.markdown("---")
    render_agent_trace_panel(trace)

    # Show synthesis results if available
    synthesis = trace.get("synthesis_output")
    if synthesis:
        render_synthesis_result(synthesis)

    # Show raw data table if available
    if result and result.get("columns") and not synthesis:
        # Only show raw table if no synthesis (synthesis already shows it better)
        render_query_result_table(result)

    # Add to conversation history
    st.session_state.conversation_history.append(
        {
            "question": prompt,
            "final_answer": final_answer,
            "trace": trace,
            "result": result,
        }
    )

# Footer
st.markdown("---")
st.caption(
    "🤖 Powered by AWS Bedrock (Nova) | Built with Streamlit & LangGraph | Multi-Agent Architecture"
)
