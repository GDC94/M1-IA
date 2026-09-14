"""Command-line entry point: one question in, one SupportResponse JSON out.

Success: JSON on stdout, exit code 0.
Failure: {"error": ..., "message": ...} JSON on stderr, exit code 1.
"""

import argparse

from pydantic import BaseModel, ValidationError

from support_assistant import ui
from support_assistant.client import create_client
from support_assistant.config import load_settings
from support_assistant.llm import (
    ModelAuthenticationError,
    ModelConnectionError,
    ModelProviderError,
    ModelRateLimitError,
)
from support_assistant.metrics_log import log_metrics
from support_assistant.support import NoAnswerError, ask_support


class ErrorResponse(BaseModel):
    error: str
    message: str


def fail(error: str, message: str) -> None:
    ui.print_error_json(ErrorResponse(error=error, message=message).model_dump_json())
    raise SystemExit(1)


def parse_question(argv: list[str] | None) -> str:
    parser = argparse.ArgumentParser(description="Ask the support assistant a question.")
    parser.add_argument("question", nargs="+", help="Customer question (quotes are optional).")
    args = parser.parse_args(argv)
    return " ".join(args.question).strip()


def main(argv: list[str] | None = None) -> None:
    question = parse_question(argv)
    if not question:
        fail("invalid_input", "The question cannot be empty.")

    try:
        settings = load_settings()
    except ValidationError as error:
        fail("invalid_config", f"Invalid configuration. Check your .env file: {error}")

    client = create_client(settings)

    try:
        with ui.thinking():
            result = ask_support(client, settings, question)
    except ModelAuthenticationError:
        fail("authentication_error", "Invalid API key. Check OPENAI_API_KEY in your .env file.")
    except ModelRateLimitError:
        fail("rate_limit", "Rate limit exceeded. Please try again later.")
    except ModelConnectionError:
        fail("connection_error", "Could not reach OpenAI. Check your connection and try again.")
    except ModelProviderError as error:
        fail("api_error", str(error))
    except NoAnswerError as error:
        fail("no_answer", str(error))
    except ValueError as error:
        # Raised by estimate_cost when the model has no configured price.
        fail("pricing_error", str(error))

    log_metrics(result.metrics, model=settings.model)
    ui.print_json(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
