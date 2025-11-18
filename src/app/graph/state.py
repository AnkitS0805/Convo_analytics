"""Graph state and trace objects with enhanced tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AgentStep:
    """Tracks a single agent execution step with timing and status."""

    agent_name: str
    status: str  # "running", "success", "error"
    started_at: str
    completed_at: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def complete(self, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """Mark step as completed with output or error."""
        self.completed_at = datetime.now().isoformat()
        self.status = "error" if error else "success"
        self.output = output
        self.error = error


@dataclass
class TurnTrace:
    """Complete trace of all agent steps in a conversational turn."""

    # Router step
    router_step: Optional[AgentStep] = None
    selected_route: Optional[str] = None  # "data" or "non-data"

    # SQL planning step (data path)
    planner_step: Optional[AgentStep] = None
    generated_sql: Optional[str] = None
    sql_corrected: bool = False
    original_sql_error: Optional[str] = None

    # Execution step (data path)
    executor_step: Optional[AgentStep] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    # Synthesis step (data path)
    synthesizer_step: Optional[AgentStep] = None
    synthesis_output: Optional[Dict[str, Any]] = None

    # Non-data QA step (non-data path)
    nondata_step: Optional[AgentStep] = None

    # Overall trace
    all_steps: List[AgentStep] = field(default_factory=list)

    def add_step(self, step: AgentStep) -> None:
        """Add a step to the trace."""
        self.all_steps.append(step)


@dataclass
class ConversationState:
    """Complete state for a single conversational turn."""

    user_message: str
    trace: TurnTrace = field(default_factory=TurnTrace)
    result: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
