
from __future__ import annotations

import ast
import json
import logging
import os
import re
import time
from typing import Any, Dict, List

import boto3
from botocore.config import Config

from ..logging_config import get_logger

logger = get_logger(__name__)

BEDROCK_REGION = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
BEDROCK_LLM_MODEL_ID = os.getenv("BEDROCK_LLM_MODEL_ID", "us.amazon.nova-lite-v1:0")
BEDROCK_EMBED_MODEL_ID = os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
BEDROCK_MAX_ATTEMPTS = int(os.getenv("BEDROCK_MAX_ATTEMPTS", "5"))
BEDROCK_CONNECT_TIMEOUT = int(os.getenv("BEDROCK_CONNECT_TIMEOUT", "10"))
BEDROCK_READ_TIMEOUT = int(os.getenv("BEDROCK_READ_TIMEOUT", "30"))

_BOTO_CFG = Config(
    retries={"max_attempts": BEDROCK_MAX_ATTEMPTS, "mode": "standard"},
    connect_timeout=BEDROCK_CONNECT_TIMEOUT,
    read_timeout=BEDROCK_READ_TIMEOUT,
)


def get_bedrock_embedding(text: str, model_id: str = BEDROCK_EMBED_MODEL_ID) -> List[float]:
   
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION, config=_BOTO_CFG)
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text}),
    )
    body = response["body"].read()
    embedding = json.loads(body)["embedding"]
    return embedding


def call_bedrock(prompt: str, model_id: str = BEDROCK_LLM_MODEL_ID) -> Dict[str, Any]:
   
    try:
        return call_bedrock_lite(prompt, model_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Bedrock call failed on lite: %s", exc)
        return call_bedrock_pro(prompt, model_id)


def call_bedrock_pro(prompt: str, model_id: str = "us.amazon.nova-pro-v1:0") -> Dict[str, Any]:
    return call_bedrock_lite(prompt, model_id)


def _strip_code_fences(text: str) -> str:
    """Remove common markdown code fences around JSON blocks."""
    t = text.strip()
    # Remove control chars that often break JSON parsing
    t = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", t)

    # Handle ```json ... ``` and variants (including '''json)
    if t.startswith("```json"):
        t = t[len("```json"):]
    if t.startswith("```"):
        t = t[len("```"):]
    if t.endswith("```"):
        t = t[: -len("```")]
    if t.startswith("'''json"):
        t = t[len("'''json"):]
    if t.startswith("'''"):
        t = t[len("'''"):]
    if t.endswith("'''"):
        t = t[: -len("'''")]
    return t.strip()


def _balance_braces_if_needed(text: str) -> str:
    """Append any missing closing braces if text starts with { or [."""
    stripped = text.strip()
    if not stripped:
        return text
    if stripped[0] == "{" and stripped.count("{") > stripped.count("}"):
        return stripped + "}" * (stripped.count("{") - stripped.count("}"))
    if stripped[0] == "[" and stripped.count("[") > stripped.count("]"):
        return stripped + "]" * (stripped.count("[") - stripped.count("]"))
    return stripped


def _attempt_json_repair(output: str) -> str | None:
    
    try:
        
        if output.count('"') % 2 != 0:  # Odd number of quotes
            # Try adding closing quote and brace
            if not output.rstrip().endswith('}'):
                repaired = output.rstrip() + '"}'
                logger.info("JSON repair: added closing quote and brace")
                return repaired
            else:
                # Just add closing quote before last brace
                repaired = output.rstrip()[:-1] + '"}'
                logger.info("JSON repair: added closing quote before brace")
                return repaired
        
        # Missing closing brace (already handled by _balance_braces_if_needed)
        # but check again just in case
        if output.count('{') > output.count('}'):
            repaired = output.rstrip() + '}'
            logger.info("JSON repair: added closing brace")
            return repaired
            
    except Exception as e:  # noqa: BLE001
        logger.debug("JSON repair attempt failed: %s", e)
        
    return None


def call_bedrock(prompt: str, model_id: str = BEDROCK_LLM_MODEL_ID) -> Dict[str, Any]:
  
    try:
        return call_bedrock_lite(prompt, model_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Bedrock call failed on lite: %s", exc)
        return call_bedrock_pro(prompt, model_id)


def call_bedrock_pro(prompt: str, model_id: str = "us.amazon.nova-pro-v1:0") -> Dict[str, Any]:
    return call_bedrock_lite(prompt, model_id)
    last = output.rfind("}")
    return output if last == -1 else output[: last + 1]


def call_bedrock_lite(prompt: str, model_id: str = BEDROCK_LLM_MODEL_ID) -> Dict[str, Any]:
    """Invoke a Bedrock chat model and parse JSON from its first text part."""
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION, config=_BOTO_CFG)
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}]
        }),
    )
    data = json.loads(response["body"].read())
    # nova chat schema: output.message.content[0].text
    msg = data.get("output", {}).get("message", {})
    content = msg.get("content")

    text = ""
    if isinstance(content, list) and content:
        first = content[0] if isinstance(content[0], dict) else {}
        text = first.get("text", "")
    elif isinstance(content, dict):
        text = content.get("text", "")
    else:
        text = msg.get("text", "") or data.get("output", {}).get("text", "")

    cleaned = _strip_code_fences(str(text))
    healed = _balance_braces_if_needed(cleaned)

    try:
        return json.loads(healed)
    except json.JSONDecodeError as e_json:  # noqa: BLE001
        logger.warning("json.loads failed: %s. Attempting JSON repair. Raw: %s", e_json, healed[:200])
        
        # Attempt to repair common JSON issues
        repaired = _attempt_json_repair(healed)
        if repaired:
            try:
                logger.info("JSON repair successful, re-parsing")
                return json.loads(repaired)
            except json.JSONDecodeError:
                logger.warning("Repaired JSON still invalid, trying ast.literal_eval")
        
        # Fallback to ast.literal_eval
        try:
            result = ast.literal_eval(healed)
            if isinstance(result, dict):
                return result
            # As a last resort, wrap into a dict
            return {"result": result}
        except Exception as e_ast:  # noqa: BLE001
            logger.error("Both json.loads and ast.literal_eval failed. Output: %s", healed[:200])
            raise RuntimeError(
                f"Bedrock did not return valid JSON or Python literal. json error: {e_json}, ast error: {e_ast}. Raw output: {healed[:300]}"
            )


class BedrockClient:
   

    def __init__(self) -> None:
        self.model_id = BEDROCK_LLM_MODEL_ID

    def complete_json(self, prompt: str, schema: Dict[str, str]) -> Dict[str, Any]:
       
        logger.info("LLM prompt (truncated 300 chars): %s", prompt[:300])
        system_prefix = (
            "You must output strictly valid JSON with the following keys and types: "
            f"{schema}. Do not include markdown fences or extraneous text."
        )
        full_prompt = f"{system_prefix}\n\n{prompt}"
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                output = call_bedrock(full_prompt, self.model_id)
                return output
            except Exception as exc:  # noqa: BLE001
                exc_str = str(exc)
                # Retry only on ModelErrorException (transient inference errors)
                if "ModelErrorException" in exc_str and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "ModelErrorException on attempt %d/%d, retrying in %.1fs: %s",
                        attempt + 1, max_retries, delay, exc
                    )
                    time.sleep(delay)
                    continue
                logger.error("BedrockClient.complete_json failed after %d attempts: %s", attempt + 1, exc)
                return {}


class BedrockLLM:
    """Lightweight adapter with an invoke(prompt) -> str interface."""

    def __init__(self, model_id: str = BEDROCK_LLM_MODEL_ID, region: str = BEDROCK_REGION) -> None:
        self.model_id = model_id
        self.region = region
        self._client = boto3.client("bedrock-runtime", region_name=self.region, config=_BOTO_CFG)

    def invoke(self, prompt: str) -> str:
        """Invoke the Bedrock chat model and return its text output."""
        try:
            response = self._client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "messages": [{"role": "user", "content": [{"text": prompt}]}]
                }),
            )
            data = json.loads(response["body"].read())
            msg = data.get("output", {}).get("message", {})
            content = msg.get("content")
            text = ""
            if isinstance(content, list) and content:
                first = content[0] if isinstance(content[0], dict) else {}
                text = first.get("text", "")
            elif isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = msg.get("text", "") or data.get("output", {}).get("text", "")
            return str(text).strip()
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            logger.error("BedrockLLM.invoke failed: %s", str(exc))
            # As a safe fallback, try the generic helper and stringify its result
            try:
                result = call_bedrock_lite(prompt, self.model_id)
                return json.dumps(result)
            except Exception:
                raise


class BedrockEmbedder:
    """Lightweight adapter exposing embed_query(text) -> List[float]."""

    def __init__(self, model_id: str = BEDROCK_EMBED_MODEL_ID) -> None:
        self.model_id = model_id

    def embed_query(self, text: str) -> List[float]:
        """Return embedding vector for the given text using Bedrock Titan."""
        try:
            emb = get_bedrock_embedding(text, model_id=self.model_id)
            return list(emb)  # explicit list for callers
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            logger.error("BedrockEmbedder.embed_query failed: %s", str(exc))
            raise


# Shared instances used across agents/memory
llm = BedrockLLM(model_id=BEDROCK_LLM_MODEL_ID)
embedder = BedrockEmbedder(model_id=BEDROCK_EMBED_MODEL_ID)

try:  # pragma: no cover
    from langchain_core.language_models.llms import LLM as _LCBase
    from pydantic import PrivateAttr as _PrivateAttr

    class LCBedrockLLM(_LCBase):
        """LangChain BaseLanguageModel-compatible wrapper around BedrockLLM."""

        _core_llm: BedrockLLM = _PrivateAttr(default=None)  # type: ignore[assignment]

        def __init__(self, core_llm: BedrockLLM) -> None:  # type: ignore[no-untyped-def]
            super().__init__()
            object.__setattr__(self, "_core_llm", core_llm)

        @property
        def _llm_type(self) -> str:  # type: ignore[override]
            return "bedrock"

        def _call(self, prompt: str, stop: list[str] | None = None, **kwargs: Any) -> str:  # type: ignore[override]
            return self._core_llm.invoke(prompt)

        @property
        def _identifying_params(self) -> Dict[str, Any]:  # type: ignore[override]
            return {"model_id": self._core_llm.model_id, "region": self._core_llm.region}

    # LangChain-compatible shared instance
    langchain_llm = LCBedrockLLM(llm)
except Exception:  # pragma: no cover
    langchain_llm = None  # type: ignore

class BedrockClient:
   

    def __init__(self) -> None:
        self.model_id = BEDROCK_LLM_MODEL_ID

    def complete_json(self, prompt: str, schema: Dict[str, str]) -> Dict[str, Any]:
       
        logger.info("LLM prompt (truncated 300 chars): %s", prompt[:300])
        system_prefix = (
            "You must output strictly valid JSON with the following keys and types: "
            f"{schema}. Do not include markdown fences or extraneous text."
        )
        full_prompt = f"{system_prefix}\n\n{prompt}"
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                return call_bedrock(full_prompt, self.model_id)
            except Exception as exc:  # noqa: BLE001
                exc_str = str(exc)
                # Retry only on ModelErrorException (transient inference errors)
                if "ModelErrorException" in exc_str and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "ModelErrorException on attempt %d/%d, retrying in %.1fs: %s",
                        attempt + 1, max_retries, delay, exc
                    )
                    time.sleep(delay)
                    continue
                logger.error("BedrockClient.complete_json failed after %d attempts: %s", attempt + 1, exc)
                return {}
