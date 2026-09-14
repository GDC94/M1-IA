"""Shared fixtures and fakes for the test suite. No real OpenAI calls anywhere."""

from types import SimpleNamespace

import pytest

from support_assistant.config import Settings
from support_assistant.llm import GenerationOptions, ModelResult, TokenUsage
from support_assistant.models import SupportAnswer


@pytest.fixture
def settings() -> Settings:
    """A validated Settings instance built directly, without touching env vars."""
    return Settings(api_key="test-key")


@pytest.fixture
def valid_support_answer() -> SupportAnswer:
    return SupportAnswer(
        answer="Te enviaremos un enlace a tu correo para restablecer tu contraseña.",
        confidence=0.9,
        actions=["reset_password"],
    )


class FakeLanguageModel:
    """Provider-neutral fake: records generation inputs and replays a result."""

    def __init__(self, output_parsed=None, usage=None, status="completed", raise_error=None):
        self.output_parsed = output_parsed
        self.usage = usage or SimpleNamespace(
            input_tokens=0, output_tokens=0, total_tokens=0
        )
        self.status = status
        self.raise_error = raise_error
        self.last_messages = None
        self.last_options: GenerationOptions | None = None

    def generate(self, messages, options):
        self.last_messages = messages
        self.last_options = options
        if self.raise_error is not None:
            raise self.raise_error
        return ModelResult(
            answer=self.output_parsed,
            usage=TokenUsage(
                input_tokens=self.usage.input_tokens,
                output_tokens=self.usage.output_tokens,
                total_tokens=self.usage.total_tokens,
            ),
            status=self.status,
        )


@pytest.fixture
def make_fake_client():
    """Factory fixture: build a provider-neutral fake."""

    def _make(output_parsed=None, usage=None, status="completed", raise_error=None):
        return FakeLanguageModel(
            output_parsed=output_parsed,
            usage=usage,
            status=status,
            raise_error=raise_error,
        )

    return _make


def make_usage(input_tokens: int, output_tokens: int, total_tokens: int) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )
