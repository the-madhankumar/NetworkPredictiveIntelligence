import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OUTPUT = ROOT / "experiments" / "c16_results.json"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def load_json(path: Path) -> object:
    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def compact_evidence(data: dict) -> dict:
    return {
        "grid_id": data.get("grid_id"),
        "timestamp": data.get("timestamp"),
        "current_activity": data.get("current_activity"),
        "baseline_activity": data.get("baseline_activity"),
        "activity_direction": data.get("activity_direction"),
        "anomaly_score": data.get("anomaly_score"),
        "risk_score": data.get("risk_score"),
        "top_features": data.get("top_features", [])[:10],
        "alerts": data.get("alerts", [])[:20],
        "pipeline_status": data.get("pipeline_status"),
        "location": data.get("location"),
    }


def main() -> None:

    source = ROOT / "Dataset" / "analytics"

    candidates = list(
        source.rglob("*.json")
    )

    if not candidates:
        raise FileNotFoundError(
            "No JSON analytics file found."
        )

    source_file = candidates[0]

    data = load_json(source_file)

    if not isinstance(data, dict):
        raise TypeError(
            "Expected analytics JSON object."
        )

    full_context = json.dumps(
        data,
        default=str
    )

    compact_context = json.dumps(
        compact_evidence(data),
        default=str
    )

    results = {
        "source_file": str(source_file),
        "full_context": {
            "characters": len(full_context),
            "estimated_tokens": estimate_tokens(
                full_context
            ),
        },
        "curated_context": {
            "characters": len(compact_context),
            "estimated_tokens": estimate_tokens(
                compact_context
            ),
        },
    }

    results["reduction"] = {
        "characters": (
            1 -
            results["curated_context"]["characters"]
            / results["full_context"]["characters"]
        ),
        "estimated_tokens": (
            1 -
            results["curated_context"]["estimated_tokens"]
            / results["full_context"]["estimated_tokens"]
        ),
    }

    OUTPUT.write_text(
        json.dumps(
            results,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        json.dumps(
            results,
            indent=2
        )
    )


if __name__ == "__main__":
    main()