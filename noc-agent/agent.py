import asyncio
import json
import sys

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

from config import MODEL


SYSTEM_PROMPT = """
You are a Network Operations Center investigation agent.

Your job is to investigate a network grid using available network intelligence tools.

You must follow this order:

1. Call pipeline_status FIRST.
2. Gather activity evidence.
3. Gather feature evidence.
4. Gather location evidence.
5. Gather anomaly evidence when available.
6. Compare current activity against baseline.
7. Assess severity.
8. Produce a structured investigation result.

Severity values:

NORMAL
ATTENTION
HIGH

Rules:

- Never invent missing values.
- Never replace missing evidence with an estimate.
- High activity does not automatically mean confirmed congestion.
- A grid is a geographic cell, not a tower.
- Activity is an activity measure.
- The baseline must exclude the current interval.
- If pipeline_status is unhealthy, explicitly include this in uncertainty.
- An unhealthy pipeline must reduce confidence in severity.
- If an important tool is unavailable, continue using the remaining evidence.
- Missing evidence must appear in uncertainty.
- Every evidence item must identify its source tool.

Return JSON:

{
  "severity": "NORMAL | ATTENTION | HIGH",
  "evidence": [
    {
      "claim": "...",
      "value": "...",
      "source_tool": "..."
    }
  ],
  "uncertainty": "...",
  "recommended_checks": [
    "..."
  ]
}
"""


async def investigate(grid_id: int) -> str:

    prompt = f"""
Investigate network grid {grid_id}.

Start with pipeline_status.

Then investigate the grid using the available network intelligence tools.

Return only the required JSON structure.
"""

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        cwd=".",
        max_turns=10,
        allowed_tools=[
            "mcp__network-intelligence__network_summary",
            "mcp__network-intelligence__grid_activity",
            "mcp__network-intelligence__grid_features",
            "mcp__network-intelligence__grid_location",
            "mcp__network-intelligence__hotspots",
            "mcp__network-intelligence__alerts",
            "mcp__network-intelligence__pipeline_status",
        ],
    )

    async for message in query(
        prompt=prompt,
        options=options,
    ):

        if isinstance(message, ResultMessage):
            return message.result or ""

    return ""


async def main() -> None:

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python agent.py <grid_id>"
        )

    grid_id = int(sys.argv[1])

    result = await investigate(grid_id)

    try:
        parsed = json.loads(result)
        print(
            json.dumps(
                parsed,
                indent=2
            )
        )
    except json.JSONDecodeError:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())