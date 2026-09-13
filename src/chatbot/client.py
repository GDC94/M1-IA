"""OpenAI client wrapper. Knows nothing about the terminal UI."""

from openai import OpenAI

from chatbot.config import Settings
from chatbot.models import Message


def create_client(settings: Settings) -> OpenAI:
    """Build the OpenAI client from validated settings."""
    return OpenAI(
        api_key=settings.api_key.get_secret_value(),
        max_retries=settings.max_retries,
    )


def get_reply(
    client: OpenAI,
    settings: Settings,
    messages: list[Message],
) -> str:
    """Send the conversation history and return the assistant's reply text."""
    response = client.responses.create(
        model=settings.model,
        temperature=settings.temperature,
        # The API expects plain dicts, so the conversion happens only here.
        input=[message.model_dump() for message in messages],
    )
    return response.output_text
