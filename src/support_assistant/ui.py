"""Terminal output with Rich. Knows nothing about OpenAI.

Rich is only used when a person is watching the terminal. When the output is piped to another
program (e.g. `uv run support "..." | jq`), plain JSON is printed so downstream systems can parse it.
"""

from contextlib import AbstractContextManager, nullcontext

from rich.console import Console

stdout = Console()
stderr = Console(stderr=True)


def thinking() -> AbstractContextManager[object]:
    """Spinner on stderr while waiting for the model. Use it with `with ui.thinking():`."""
    if not stderr.is_terminal:
        return nullcontext()
    return stderr.status("Thinking...", spinner="dots")


def print_json(payload: str) -> None:
    """Print a JSON result: colored for people, plain for programs."""
    if stdout.is_terminal:
        stdout.print_json(payload)
    else:
        print(payload)


def print_error_json(payload: str) -> None:
    """Print a JSON error on stderr: colored for people, plain for programs."""
    if stderr.is_terminal:
        stderr.print(payload, style="bold red", highlight=False, markup=False)
    else:
        print(payload, file=stderr.file)
