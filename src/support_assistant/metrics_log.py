"""Append per-run metrics to a JSON Lines file (one JSON object per line) for monitoring."""

import json
from datetime import UTC, datetime
from pathlib import Path

from support_assistant.models import Metrics
from support_assistant.safety import SafetyResult

DEFAULT_METRICS_LOG_PATH = Path("logs/metrics.jsonl")
DEFAULT_SAFETY_LOG_PATH = Path("logs/safety.jsonl")


class MetricsLogEntry(Metrics):
    # The question is intentionally not logged to keep customer data out of the logs.
    timestamp: datetime
    model: str


def log_metrics(
    metrics: Metrics, model: str, path: Path = DEFAULT_METRICS_LOG_PATH
) -> MetricsLogEntry:
    entry = MetricsLogEntry(
        **metrics.model_dump(), timestamp=datetime.now(UTC), model=model
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(entry.model_dump_json() + "\n")
    return entry


def log_safety_decision(
    decision: SafetyResult, path: Path = DEFAULT_SAFETY_LOG_PATH
) -> None:
    """Append a safety event without recording user or model content."""
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "allowed": decision.allowed,
        "stage": decision.stage,
        "reason": decision.reason,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")
