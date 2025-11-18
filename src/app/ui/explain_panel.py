"""Explainability panel rendering for Streamlit."""
from __future__ import annotations

import streamlit as st

from ..graph.state import TurnTrace


def render_explain_panel(trace: TurnTrace) -> None:
    st.subheader("Explainability")
    st.markdown(f"**Agent:** {trace.selected_agent}")
    if trace.rationale_summary:
        st.markdown(f"**Thought Summary:** {trace.rationale_summary}")
    if trace.generated_sql is not None:
        st.markdown("**Generated SQL (before execution):**")
        st.code(trace.generated_sql, language="sql")
    if trace.execution_metadata:
        with st.expander("Execution Metadata"):
            st.json(trace.execution_metadata)
    if trace.synthesis_summary:
        st.markdown(f"**Synthesis Summary:** {trace.synthesis_summary}")
