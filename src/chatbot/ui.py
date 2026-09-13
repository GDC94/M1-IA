"""Terminal rendering with Rich. Knows nothing about OpenAI."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.status import Status
from rich.table import Table

from chatbot.models import Message

console = Console()

ROLE_STYLES = {"system": "magenta", "user": "cyan", "assistant": "green"}


def show_welcome(model: str) -> None:
    console.print(
        Panel(
            f"Model: [bold]{model}[/bold]\nType [cyan]/help[/cyan] to see the commands.",
            title="Chatbot ready",
            border_style="blue",
        )
    )


def ask_user() -> str:
    return Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()


def thinking() -> Status:
    """Spinner shown while waiting for the model. Use it with `with ui.thinking():`."""
    return console.status("Thinking...", spinner="dots")


def show_assistant(text: str) -> None:
    console.print(Panel(Markdown(text), title="Assistant", title_align="left", border_style="green"))


def show_help(commands: dict[str, str]) -> None:
    """`commands` maps each command name to its description."""
    table = Table(title="Commands", show_header=False, box=None)
    for name, description in commands.items():
        table.add_row(f"[cyan]{name}[/cyan]", description)
    console.print(table)


def show_history(messages: list[Message]) -> None:
    table = Table(title="Conversation history", show_lines=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Role")
    table.add_column("Content")
    for index, message in enumerate(messages):
        style = ROLE_STYLES[message.role]
        table.add_row(str(index), f"[{style}]{message.role}[/{style}]", message.content)
    console.print(table)


def show_settings(values: dict[str, object]) -> None:
    table = Table(title="Current settings", show_header=False, box=None)
    for name, value in values.items():
        table.add_row(f"[cyan]{name}[/cyan]", str(value))
    console.print(table)


def show_info(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def show_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")
