"""Tests for support_assistant.metrics_log.log_metrics: append-only JSONL, no question logged."""

import json
from pathlib import Path

from support_assistant.metrics_log import log_metrics, log_safety_decision
from support_assistant.models import Metrics
from support_assistant.safety import SafetyResult


def _sample_metrics() -> Metrics:
    return Metrics(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        latency_ms=42.0,
        estimated_cost_usd=0.0001,
    )


def test_log_metrics_writes_one_valid_json_line(tmp_path: Path):
    log_path = tmp_path / "metrics.jsonl"

    log_metrics(_sample_metrics(), model="gpt-4o-mini", path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["prompt_tokens"] == 10
    assert entry["completion_tokens"] == 5
    assert entry["total_tokens"] == 15
    assert entry["model"] == "gpt-4o-mini"
    assert "timestamp" in entry


def test_log_metrics_appends_on_repeated_calls(tmp_path: Path):
    log_path = tmp_path / "metrics.jsonl"

    log_metrics(_sample_metrics(), model="gpt-4o-mini", path=log_path)
    log_metrics(_sample_metrics(), model="gpt-4o-mini", path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_log_metrics_creates_missing_parent_dirs(tmp_path: Path):
    log_path = tmp_path / "nested" / "logs" / "metrics.jsonl"

    log_metrics(_sample_metrics(), model="gpt-4o-mini", path=log_path)

    assert log_path.exists()


def test_log_metrics_entry_does_not_include_question(tmp_path: Path):
    log_path = tmp_path / "metrics.jsonl"

    log_metrics(_sample_metrics(), model="gpt-4o-mini", path=log_path)

    entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert "question" not in entry


def test_log_safety_decision_writes_reason_without_sensitive_content(tmp_path: Path):
    log_path = tmp_path / "safety.jsonl"

    log_safety_decision(
        SafetyResult(False, "input", "prompt_injection"), path=log_path
    )

    entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert entry["allowed"] is False
    assert entry["stage"] == "input"
    assert entry["reason"] == "prompt_injection"
    assert "question" not in entry
