"""Tests for support_assistant.pricing: pure cost math, no network."""

import pytest

from support_assistant.pricing import estimate_cost


def test_one_million_input_tokens_on_gpt_4o_mini_costs_015():
    assert estimate_cost("gpt-4o-mini", 1_000_000, 0) == 0.15


def test_one_million_output_tokens_on_gpt_4o_mini_costs_060():
    assert estimate_cost("gpt-4o-mini", 0, 1_000_000) == 0.60


def test_combined_tokens_match_manual_calculation():
    input_tokens = 200_000
    output_tokens = 50_000

    expected = round(
        input_tokens * 0.15 / 1_000_000 + output_tokens * 0.60 / 1_000_000, 8
    )

    assert estimate_cost("gpt-4o-mini", input_tokens, output_tokens) == expected


def test_zero_tokens_cost_nothing():
    assert estimate_cost("gpt-4o-mini", 0, 0) == 0.0


def test_unknown_model_raises_value_error():
    with pytest.raises(ValueError):
        estimate_cost("not-a-real-model", 100, 100)
