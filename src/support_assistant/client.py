"""OpenAI client factory. Knows nothing about the terminal UI."""

from openai import OpenAI

from support_assistant.config import Settings
from support_assistant.llm import OpenAIAdapter


def create_client(settings: Settings) -> OpenAIAdapter:
    """Build the provider adapter from validated settings."""
    client = OpenAI(
        api_key=settings.api_key.get_secret_value(),
        max_retries=settings.max_retries,
    )
    return OpenAIAdapter(client)
