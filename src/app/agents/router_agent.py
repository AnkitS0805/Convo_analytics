
from __future__ import annotations

from dataclasses import dataclass

from ..llm.bedrock_client import BedrockClient
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RouteDecision:
    """Result of routing decision with detailed reasoning."""

    route: str  # "data" | "non-data"
    confidence: str  # "high" | "medium" | "low"
    rationale: str
    user_intent: str


class RouterAgent:
   

    def __init__(self, llm: BedrockClient) -> None:
        self.llm = llm
        logger.info("RouterAgent initialized")

    def route(self, message: str) -> RouteDecision:
        
        logger.info("Routing user message: %s", message[:100])

        prompt = (
            "You are an intelligent query router for a data analytics system.\n\n"
            "Analyze the user's message and determine if it:\n"
            "- Requires DATABASE ACCESS (route='data'): Questions about products, sales, customers, "
            "orders, categories, territories, or any business metrics/analytics\n"
            "- Can be answered DIRECTLY (route='non-data'): Greetings, general questions, "
            "system help, or topics unrelated to the database\n\n"
            f"User Message: \"{message}\"\n\n"
            "Provide:\n"
            "1. route: 'data' or 'non-data'\n"
            "2. confidence: 'high', 'medium', or 'low'\n"
            "3. rationale: Brief explanation (1-2 sentences) of why you chose this route\n"
            "4. user_intent: One-sentence summary of what the user wants to know\n\n"
            "Return JSON with keys: route, confidence, rationale, user_intent"
        )

        schema = {
            "route": "str",
            "confidence": "str",
            "rationale": "str",
            "user_intent": "str",
        }

        rsp = self.llm.complete_json(prompt, schema=schema)

        # Validate and normalize route
        route = rsp.get("route", "data").lower()
        if route not in {"data", "non-data"}:
            logger.warning("Invalid route '%s', defaulting to 'data'", route)
            route = "data"

        decision = RouteDecision(
            route=route,
            confidence=rsp.get("confidence", "medium"),
            rationale=rsp.get("rationale", "No rationale provided"),
            user_intent=rsp.get("user_intent", message),
        )

        logger.info(
            "Routing decision: route=%s, confidence=%s, intent='%s'",
            decision.route,
            decision.confidence,
            decision.user_intent[:50],
        )

        return decision
