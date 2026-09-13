"""Entry point: the chat loop (input -> history -> client -> ui)."""

from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from chatbot import ui
from chatbot.client import create_client, get_reply
from chatbot.commands import COMMANDS
from chatbot.config import load_settings
from chatbot.models import Message

SYSTEM_PROMPT = "You are a helpful assistant."


def new_history() -> list[Message]:
    return [Message(role="system", content=SYSTEM_PROMPT)]


def main() -> None:
    try:
        settings = load_settings()
    except ValidationError as error:
        ui.show_error(f"Invalid configuration. Check your .env file:\n{error}")
        return

    client = create_client(settings)
    history = new_history()

    ui.show_welcome(settings.model)

    while True:
        try:
            user_input = ui.ask_user()
        except EOFError, KeyboardInterrupt:
            break

        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/clear":
            history = new_history()
            ui.show_info("History cleared.")
            continue
        if user_input == "/help":
            ui.show_help(COMMANDS)
            continue
        if user_input == "/history":
            ui.show_history(history)
            continue
        if user_input == "/model":
            ui.show_settings(settings.model_dump(exclude={"api_key"}))
            continue
        if user_input == "/undo":
            # Only the system message left: nothing to undo.
            if len(history) < 3:
                ui.show_info("Nothing to undo.")
            else:
                history.pop()  # assistant reply
                history.pop()  # user message
                ui.show_info("Last exchange removed.")
            continue
        if user_input.startswith("/"):
            ui.show_error(
                f"Unknown command: {user_input}. Type /help to see the commands."
            )
            continue

        history.append(Message(role="user", content=user_input))

        try:
            with ui.thinking():
                reply = get_reply(client, settings, history)
        except AuthenticationError:
            # Una clave inválida no se puede arreglar, por lo que se detiene en lugar de fallar en cada mensaje.
            ui.show_error("Invalid API key. Check OPENAI_API_KEY in your .env file.")
            raise SystemExit(1)
        except RateLimitError:
            history.pop()
            ui.show_error("Rate limit exceeded. Please try again later.")
            raise
        except APIConnectionError:
            history.pop()
            ui.show_error("API connection error. Please try again later.")
            raise
        except APIError as error:
            history.pop()
            ui.show_error(f"API error: {error}")
            raise

        history.append(Message(role="assistant", content=reply))
        ui.show_assistant(reply)

    ui.show_info("\nBye!")


if __name__ == "__main__":
    main()
