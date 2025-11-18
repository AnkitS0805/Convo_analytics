"""Rich UI component for displaying agent execution traces."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st


def render_agent_step(step: Dict[str, Any], step_number: int) -> None:
    """Render a single agent step with status, timing, and output.

    Args:
        step: AgentStep dictionary with agent_name, status, output, etc.
        step_number: Step number for display
    """
    agent_name = step.get("agent_name", "Unknown Agent")
    status = step.get("status", "unknown")
    started = step.get("started_at", "")
    completed = step.get("completed_at", "")
    output = step.get("output", {})
    error = step.get("error")

    # Status icon and color
    status_icons = {
        "running": "🔄",
        "success": "✅",
        "error": "❌",
    }
    status_colors = {
        "running": "blue",
        "success": "green",
        "error": "red",
    }

    icon = status_icons.get(status, "⚪")
    color = status_colors.get(status, "gray")

    # Create expander with status
    with st.expander(f"{icon} **Step {step_number}: {agent_name}**", expanded=True):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown(f"**Status:** :{color}[{status.upper()}]")
            if completed:
                # Calculate duration
                from datetime import datetime

                try:
                    start_dt = datetime.fromisoformat(started)
                    end_dt = datetime.fromisoformat(completed)
                    duration = (end_dt - start_dt).total_seconds()
                    st.markdown(f"**Duration:** {duration:.2f}s")
                except Exception:  # noqa: BLE001
                    pass

        with col2:
            if error:
                st.error(f"**Error:** {error}")
            elif output:
                _render_agent_output(agent_name, output)


def _render_agent_output(agent_name: str, output: Dict[str, Any]) -> None:
    """Render agent-specific output in a structured format."""
    if agent_name == "Router":
        st.markdown(f"**🎯 Route:** `{output.get('route', 'unknown')}`")
        st.markdown(f"**📊 Confidence:** {output.get('confidence', 'medium')}")
        st.info(f"**Intent:** {output.get('user_intent', '')}")
        with st.expander("Routing Rationale"):
            st.write(output.get("rationale", "No rationale provided"))

    elif agent_name == "SQL Planner":
        st.markdown(f"**🎯 Confidence:** {output.get('confidence', 'medium')}")
        st.markdown(f"**📊 Tables:** {', '.join(output.get('tables_used', []))}")
        st.markdown(f"**📈 Metrics:** {', '.join(output.get('key_metrics', []))}")

        with st.expander("📝 SQL Query", expanded=True):
            st.code(output.get("sql", ""), language="sql")

        with st.expander("💡 Explanation"):
            st.write(output.get("explanation", "No explanation provided"))

    elif agent_name == "SQL Executor":
        corrected = output.get("corrected", False)
        if corrected:
            st.warning("⚠️ SQL was auto-corrected due to initial error")

        st.markdown(f"**📊 Rows:** {output.get('row_count', 0):,}")
        st.markdown(f"**📋 Columns:** {output.get('column_count', 0)}")

        cols = output.get("columns", [])
        if cols:
            st.markdown(f"**Column Names:** {', '.join(cols)}")

    elif agent_name == "Synthesizer":
        summary = output.get("summary", "")
        if summary:
            st.success(f"**📊 Executive Summary:**\n\n{summary}")

        findings = output.get("key_findings", [])
        if findings:
            st.markdown("**🔍 Key Findings:**")
            for finding in findings:
                st.markdown(f"- {finding}")

        analysis = output.get("detailed_analysis", "")
        if analysis:
            with st.expander("📈 Detailed Analysis"):
                st.write(analysis)

        recs = output.get("recommendations", [])
        if recs:
            with st.expander("💡 Recommendations"):
                for i, rec in enumerate(recs, 1):
                    st.markdown(f"{i}. {rec}")

        if output.get("has_chart"):
            st.info("📊 Chart visualization available below")

    elif agent_name == "Non-Data QA":
        st.markdown(f"**📁 Category:** {output.get('category', 'general')}")
        answer = output.get("answer", "")
        if answer:
            st.info(answer)
        with st.expander("Rationale"):
            st.write(output.get("rationale", "No rationale provided"))


def render_agent_trace_panel(trace: Dict[str, Any]) -> None:
    """Render complete agent execution trace with all steps.

    Args:
        trace: Complete trace dictionary with all_steps and other metadata
    """
    st.markdown("---")
    st.markdown("## 🤖 Agent Execution Trace")

    all_steps = trace.get("all_steps", [])

    if not all_steps:
        st.info("No agent steps recorded yet.")
        return

    # Show high-level summary
    total_steps = len(all_steps)
    success_steps = sum(1 for s in all_steps if s.get("status") == "success")
    error_steps = sum(1 for s in all_steps if s.get("status") == "error")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Steps", total_steps)
    col2.metric("Successful", success_steps, delta_color="normal")
    col3.metric("Errors", error_steps, delta_color="inverse")

    st.markdown("---")

    # Render each step
    for idx, step in enumerate(all_steps, 1):
        render_agent_step(step, idx)

    # Show additional metadata
    if trace.get("sql_corrected"):
        st.warning(
            f"⚠️ **SQL Auto-Correction Applied**\n\n"
            f"Original error: {trace.get('original_sql_error', 'Unknown error')}"
        )


def render_synthesis_result(synthesis_output: Optional[Dict[str, Any]]) -> None:
    """Render synthesis results with chart if available.

    Args:
        synthesis_output: Synthesis output dictionary with summary, findings, chart_spec
    """
    if not synthesis_output:
        return

    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # Executive summary (prominent)
    summary = synthesis_output.get("summary", "")
    if summary:
        st.markdown("### Executive Summary")
        st.success(summary)

    # Key findings
    findings = synthesis_output.get("key_findings", [])
    if findings:
        st.markdown("### 🔍 Key Findings")
        for finding in findings:
            st.markdown(f"- {finding}")

    # Detailed analysis
    analysis = synthesis_output.get("detailed_analysis", "")
    if analysis:
        st.markdown("### 📈 Detailed Analysis")
        st.write(analysis)

    # Recommendations
    recs = synthesis_output.get("recommendations", [])
    if recs:
        st.markdown("### 💡 Recommendations")
        for i, rec in enumerate(recs, 1):
            st.markdown(f"{i}. {rec}")

    # Chart visualization
    chart_spec = synthesis_output.get("chart_spec")
    if chart_spec:
        st.markdown("### 📊 Visualization")
        try:
            import altair as alt

            chart = alt.Chart.from_dict(chart_spec)
            st.altair_chart(chart, width='stretch')
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not render chart: {e}")


def render_query_result_table(result: Optional[Dict[str, Any]]) -> None:
    """Render raw query results as a data table.

    Args:
        result: Result dictionary with columns and rows
    """
    if not result:
        return

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    if not columns or not rows:
        return

    st.markdown("---")
    st.markdown("## 📋 Raw Data")

    import pandas as pd

    df = pd.DataFrame(rows, columns=columns)

    # Show record count
    st.caption(f"Showing {len(df):,} record(s)")

    # Display table
    st.dataframe(df, width="stretch", height=400)
