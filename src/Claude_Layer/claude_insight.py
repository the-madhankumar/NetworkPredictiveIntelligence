import json
import os

import anthropic
from dotenv import load_dotenv

from tools.tools_description import tools
from tools.tool_executor import execute_tool


load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL")

if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY is not configured")

if not MODEL:
    raise ValueError("ANTHROPIC_MODEL is not configured")


client = anthropic.Anthropic(api_key=API_KEY)


SYSTEM_PROMPT = """
You are a Network Operations Centre assistant.

You answer network operations questions using the available tools.

IMPORTANT RULES:

1. Always use tools when answering questions about current network activity, grids,
   anomalies, features, alerts, or network status.

2. Never invent network data.

3. Every factual network value must come from a tool result.

4. Clearly distinguish observations from inference.

5. Do not claim congestion, overload, capacity exhaustion, or performance
   degradation unless explicit capacity or utilization evidence is provided.

6. Activity values are activity measures. Do not describe them as call counts,
   message counts, data volume, MB, users, or subscribers.

7. If a tool fails, report the failure and do not guess the missing value.

8. For a specific grid:
   - Use the grid ID as the primary identifier.
   - Use get_grid_activity for recent activity.
   - Use get_grid_features for calculated features.
   - Use get_anomaly_score when an exact timestamp is available.
   - Use get_total_activity when total activity is specifically required.

9. If get_grid_activity returns a timestamp, use that timestamp when calling
   get_anomaly_score if an anomaly score is required.

10. Use only information returned by tools for factual claims.

11. Do not run tools unnecessarily.

12. When explaining a grid, provide:
   - Current/recent activity evidence
   - Feature evidence
   - Anomaly evidence when available
   - Interpretation
   - Recommended next checks

13. If required evidence is unavailable, explicitly state that the evidence is
   insufficient.

When answering, keep the response concise and operationally useful.
"""


def run_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Execute a Claude-requested tool through the local tool dispatcher.
    """

    try:
        result = execute_tool(tool_name, tool_input)

        if isinstance(result, dict):
            return result

        return {
            "tool": tool_name,
            "status": "success",
            "data": result
        }

    except Exception as exc:
        return {
            "tool": tool_name,
            "status": "failed",
            "error": str(exc)
        }


def ask_claude(user_question: str) -> str:

    if not user_question or not user_question.strip():
        raise ValueError("user_question cannot be empty")

    messages = [
        {
            "role": "user",
            "content": user_question.strip()
        }
    ]

    while True:

        response = client.messages.create(
            model=MODEL,
            system=SYSTEM_PROMPT,
            max_tokens=1200,
            tools=tools,
            messages=messages
        )

        assistant_content = response.content

        messages.append(
            {
                "role": "assistant",
                "content": assistant_content
            }
        )

        tool_results = []

        for block in assistant_content:

            if block.type != "tool_use":
                continue

            result = run_tool(
                tool_name=block.name,
                tool_input=block.input
            )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str
                    )
                }
            )

        if not tool_results:

            text_blocks = [
                block.text
                for block in response.content
                if isinstance(block, anthropic.types.TextBlock)
            ]

            if not text_blocks:
                raise RuntimeError(
                    "Claude returned no text content"
                )

            return "\n".join(text_blocks)

        messages.append(
            {
                "role": "user",
                "content": tool_results
            }
        )


if __name__ == "__main__":

    question = "Explain Grid 4821"

    answer = ask_claude(question)

    print("\n" + answer)