
from __future__ import annotations

from dataclasses import dataclass

from ..llm.bedrock_client import BedrockClient
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class NonDataAnswer:
   
    answer: str
    category: str  
    rationale: str


class NonDataQAAgent:
    

    def __init__(self, llm: BedrockClient) -> None:
        self.llm = llm
        logger.info("NonDataQAAgent initialized")

    def answer(self, message: str) -> NonDataAnswer:
       
        logger.info("Answering non-data question: %s", message[:100])

        prompt = (
            "You are a helpful assistant for a business analytics platform.\n\n"
            "The user has asked a question that doesn't require database access. "
            "Provide a friendly, helpful, and informative response.\n\n"
            f"User Message: \"{message}\"\n\n"
            "Guidelines:\n"
            "- For greetings: Be warm and offer help\n"
            "- For help requests: Explain system capabilities (SQL analytics, data visualization)\n"
            "- For general questions: Provide accurate, concise information\n"
            "- Be professional but friendly\n"
            "- Keep answers clear and well-structured (2-4 sentences)\n\n"
            "Provide:\n"
            "1. answer: Your complete response (2-4 sentences, helpful and friendly)\n"
            "2. category: Type of question ('greeting', 'help', 'general_knowledge', 'other')\n"
            "3. rationale: Brief note on how you interpreted the question\n\n"
            "Return JSON with keys: answer, category, rationale"
        )

        schema = {"answer": "str", "category": "str", "rationale": "str"}

        rsp = self.llm.complete_json(prompt, schema=schema)

        result = NonDataAnswer(
            answer=rsp.get("answer", "I'm here to help with data analytics queries!"),
            category=rsp.get("category", "general"),
            rationale=rsp.get("rationale", "Responding to user query"),
        )

        logger.info("Non-data response generated: category=%s", result.category)

        return result
