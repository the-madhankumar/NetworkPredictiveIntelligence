import os
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

if not API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY is not configured")

client = Anthropic(api_key=API_KEY)

SYSTEM_PROMPT = """
You are a Customer Retention Intelligence Assistant for a telecom operator.

Business context:
- The telecom operator has approximately 7,043 customers.
- The historical churn baseline is approximately 26.5%.
- Your purpose is to help users understand customer churn risk,
  customer behaviour, retention signals, and retention priorities.

Rules:
1. Never invent customer data.
2. Never claim that a customer has a specific behaviour unless that
   information is provided in the available evidence.
3. If customer information is missing, explicitly say that there is
   insufficient evidence.
4. Distinguish between observed facts and interpretations.
5. Do not present a prediction as a confirmed fact.
6. Do not expose secrets, API keys, or internal credentials.
7. Keep answers clear and useful for a telecom retention analyst.
"""


def build_messages(
    message: str,
    conversation_history: list[dict[str, str]],
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    for item in conversation_history:
        role = item.get("role")
        content = item.get("content")

        if role not in {"user", "assistant"}:
            continue

        if not content:
            continue

        messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    return messages


def extract_usage(response: Any) -> dict[str, int]:
    usage = response.usage

    return {
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
        "cache_creation_input_tokens": getattr(
            usage,
            "cache_creation_input_tokens",
            0,
        ),
        "cache_read_input_tokens": getattr(
            usage,
            "cache_read_input_tokens",
            0,
        ),
    }


def chat(
    message: str,
    conversation_history: list[dict[str, str]],
    thinking: bool = False,
    use_cache: bool = True,
) -> dict[str, Any]:

    messages = build_messages(
        message,
        conversation_history,
    )

    system_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
        }
    ]

    if use_cache:
        system_content[0]["cache_control"] = {
            "type": "ephemeral",
            "ttl": "5m",
        }

    request: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": 2048,
        "system": system_content,
        "messages": messages,
    }

    if thinking:
        request["thinking"] = {
            "type": "adaptive",
        }

    response = client.messages.create(**request)

    reply_parts: list[str] = []

    for block in response.content:
        if getattr(block, "type", None) == "text":
            reply_parts.append(block.text)

    reply = "\n".join(reply_parts).strip()

    return {
        "reply": reply,
        "model": MODEL,
        "thinking_enabled": thinking,
        "cache_enabled": use_cache,
        "usage": extract_usage(response),
    }