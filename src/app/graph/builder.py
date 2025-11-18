"""LangGraph builder for the multi-agent analytics flow with enhanced tracking."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict

from langgraph.graph import END, StateGraph
from sqlalchemy.exc import OperationalError

from ..agents.non_data_agent import NonDataQAAgent
from ..agents.router_agent import RouterAgent
from ..agents.sql_planner_agent import SqlPlannerAgent
from ..agents.synthesizer_agent import SynthesizerAgent
from ..graph.state import AgentStep, TurnTrace
from ..logging_config import get_logger

logger = get_logger(__name__)


def build_graph(
    router: RouterAgent,
    planner_factory: Callable[[str], SqlPlannerAgent],
    non_data: NonDataQAAgent,
    synthesizer: SynthesizerAgent,
    sql_executor: Callable[[str], Dict],
):
    # Use dict state to align with LangGraph
    g = StateGraph(dict)

    def _init_trace(state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize trace structure if needed."""
        if "trace" not in state or not isinstance(state["trace"], dict):
            state["trace"] = {
                "router_step": None,
                "selected_route": None,
                "planner_step": None,
                "generated_sql": None,
                "sql_corrected": False,
                "original_sql_error": None,
                "executor_step": None,
                "execution_metadata": None,
                "synthesizer_step": None,
                "synthesis_output": None,
                "nondata_step": None,
                "all_steps": [],
            }
        return state["trace"]

    def route_node(state: Dict[str, Any]):
        """Route queries to data or non-data path."""
        logger.info("=" * 60)
        logger.info("ROUTER NODE: Starting routing decision")

        step = AgentStep(
            agent_name="Router",
            status="running",
            started_at=datetime.now().isoformat(),
        )

        trace = _init_trace(state)
        trace["router_step"] = step.__dict__
        trace["all_steps"].append(step.__dict__)

        try:
            decision = router.route(state["user_message"])
            output = {
                "route": decision.route,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
                "user_intent": decision.user_intent,
            }
            step.complete(output=output)

            trace["router_step"] = step.__dict__
            trace["selected_route"] = decision.route
            state["result"] = {"route": decision.route}

            logger.info("ROUTER NODE: Completed - route=%s", decision.route)
        except Exception as e:  # noqa: BLE001
            logger.error("ROUTER NODE: Failed - %s", str(e))
            step.complete(error=str(e))
            trace["router_step"] = step.__dict__
            state["result"] = {"route": "data"}  # Default to data path

        state["trace"] = trace
        return state

    def plan_node(state: Dict[str, Any]):
        """Generate SQL from natural language."""
        logger.info("=" * 60)
        logger.info("PLANNER NODE: Starting SQL generation")

        step = AgentStep(
            agent_name="SQL Planner",
            status="running",
            started_at=datetime.now().isoformat(),
        )

        trace = state.get("trace", {})
        trace["planner_step"] = step.__dict__
        trace["all_steps"].append(step.__dict__)

        try:
            planner = planner_factory("current_schema")
            plan = planner.plan(state["user_message"])

            output = {
                "sql": plan.sql,
                "explanation": plan.explanation,
                "tables_used": plan.tables_used,
                "key_metrics": plan.key_metrics,
                "confidence": plan.confidence,
            }
            step.complete(output=output)

            trace["planner_step"] = step.__dict__
            trace["generated_sql"] = plan.sql

            logger.info("PLANNER NODE: Completed - confidence=%s", plan.confidence)
        except Exception as e:  # noqa: BLE001
            logger.error("PLANNER NODE: Failed - %s", str(e))
            step.complete(error=str(e))
            trace["planner_step"] = step.__dict__
            trace["generated_sql"] = "SELECT 1"

        state["trace"] = trace
        return state

    def execute_node(state: Dict[str, Any]):
        """Execute SQL with automatic error correction."""
        logger.info("=" * 60)
        logger.info("EXECUTOR NODE: Starting SQL execution")

        step = AgentStep(
            agent_name="SQL Executor",
            status="running",
            started_at=datetime.now().isoformat(),
        )

        trace = state.get("trace", {})
        trace["executor_step"] = step.__dict__
        trace["all_steps"].append(step.__dict__)

        sql = trace.get("generated_sql", "SELECT 1")
        result = None

        try:
            result = sql_executor(sql)
            output = {
                "row_count": result.get("row_count"),
                "column_count": len(result.get("columns", [])),
                "columns": result.get("columns", []),
            }
            step.complete(output=output)

            logger.info(
                "EXECUTOR NODE: Completed - %d rows, %d columns",
                result.get("row_count", 0),
                len(result.get("columns", [])),
            )

        except OperationalError as e:
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.warning("EXECUTOR NODE: SQL failed, attempting correction: %s", error_msg)

            trace["sql_corrected"] = True
            trace["original_sql_error"] = error_msg

            # Attempt correction
            try:
                planner = planner_factory("current_schema")
                correction_prompt = (
                    f"The following SQL failed with error: {error_msg}\n\n"
                    f"Original SQL:\n{sql}\n\n"
                    f"User question: {state.get('user_message', '')}\n\n"
                    "Fix the SQL to use only valid columns from the schema."
                )
                corrected_plan = planner.plan(correction_prompt)
                corrected_sql = corrected_plan.sql
                trace["generated_sql"] = corrected_sql

                logger.info("EXECUTOR NODE: Retrying with corrected SQL")
                result = sql_executor(corrected_sql)

                output = {
                    "row_count": result.get("row_count"),
                    "column_count": len(result.get("columns", [])),
                    "columns": result.get("columns", []),
                    "corrected": True,
                }
                step.complete(output=output)
                logger.info("EXECUTOR NODE: Correction successful")

            except Exception as retry_error:  # noqa: BLE001
                logger.error("EXECUTOR NODE: Correction failed: %s", retry_error)
                result = {
                    "columns": ["Error"],
                    "rows": [(f"SQL execution failed: {error_msg}",)],
                    "row_count": 1,
                }
                step.complete(error=f"Correction failed: {str(retry_error)}")

        trace["executor_step"] = step.__dict__
        trace["execution_metadata"] = {
            "row_count": result.get("row_count") if result else 0,
            "columns": result.get("columns", []) if result else [],
        }
        state["result"] = result
        state["trace"] = trace
        return state

    def synth_node(state: Dict[str, Any]):
        """Synthesize results into business insights."""
        logger.info("=" * 60)
        logger.info("SYNTHESIZER NODE: Starting result synthesis")

        step = AgentStep(
            agent_name="Synthesizer",
            status="running",
            started_at=datetime.now().isoformat(),
        )

        trace = state.get("trace", {})
        trace["synthesizer_step"] = step.__dict__
        trace["all_steps"].append(step.__dict__)

        result = state.get("result", {})
        cols = result.get("columns", [])
        rows = result.get("rows", [])

        try:
            syn = synthesizer.synthesize(cols, rows)

            output = {
                "summary": syn.summary,
                "key_findings": syn.key_findings,
                "detailed_analysis": syn.detailed_analysis,
                "recommendations": syn.recommendations,
                "has_chart": syn.chart_spec is not None,
            }
            step.complete(output=output)

            trace["synthesizer_step"] = step.__dict__
            trace["synthesis_output"] = {
                "summary": syn.summary,
                "key_findings": syn.key_findings,
                "detailed_analysis": syn.detailed_analysis,
                "recommendations": syn.recommendations,
                "chart_spec": syn.chart_spec,
            }

            # Set final answer
            state["final_answer"] = syn.summary

            logger.info("SYNTHESIZER NODE: Completed with %d findings", len(syn.key_findings))

        except Exception as e:  # noqa: BLE001
            logger.error("SYNTHESIZER NODE: Failed - %s", str(e))
            step.complete(error=str(e))
            trace["synthesizer_step"] = step.__dict__

        state["trace"] = trace
        return state

    def non_data_node(state: Dict[str, Any]):
        """Handle non-database questions."""
        logger.info("=" * 60)
        logger.info("NON-DATA NODE: Starting response generation")

        step = AgentStep(
            agent_name="Non-Data QA",
            status="running",
            started_at=datetime.now().isoformat(),
        )

        trace = _init_trace(state)
        trace["nondata_step"] = step.__dict__
        trace["all_steps"].append(step.__dict__)

        try:
            ans = non_data.answer(state["user_message"])

            output = {
                "answer": ans.answer,
                "category": ans.category,
                "rationale": ans.rationale,
            }
            step.complete(output=output)

            trace["nondata_step"] = step.__dict__
            state["result"] = {"answer": ans.answer}
            state["final_answer"] = ans.answer

            logger.info("NON-DATA NODE: Completed - category=%s", ans.category)

        except Exception as e:  # noqa: BLE001
            logger.error("NON-DATA NODE: Failed - %s", str(e))
            step.complete(error=str(e))
            trace["nondata_step"] = step.__dict__
            state["result"] = {"answer": "I'm here to help with your questions!"}

        state["trace"] = trace
        return state

    g.add_node("route", route_node)
    g.add_node("plan", plan_node)
    g.add_node("execute", execute_node)
    g.add_node("synthesize", synth_node)
    g.add_node("nondata", non_data_node)

    g.set_entry_point("route")
    # Conditional routing from 'route' node
    def route_condition(state: Dict[str, Any]):
        return "data" if (state.get("result") or {}).get("route") == "data" else "nondata"

    g.add_conditional_edges(
        "route",
        route_condition,
        {
            "data": "plan",
            "nondata": "nondata",
        },
    )

    # Linear edges for data path
    g.add_edge("plan", "execute")
    g.add_edge("execute", "synthesize")
    g.add_edge("synthesize", END)
    # End non-data path
    g.add_edge("nondata", END)

    return g.compile()
