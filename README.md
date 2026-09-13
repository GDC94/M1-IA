# Chatbot

A simple terminal chatbot built with the OpenAI API, Pydantic, python-dotenv, and Rich.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Setup

```bash
uv sync
cp .env.example .env
```

Then add your API key to `.env`:

```
OPENAI_API_KEY=sk-...
```

## Run

```bash
uv run chatbot
```

## Commands

| Command    | Description                            |
| ---------- | -------------------------------------- |
| `/help`    | Show the list of commands              |
| `/history` | Show the current conversation          |
| `/model`   | Show the active settings               |
| `/undo`    | Remove your last message and its reply |
| `/clear`   | Start a new conversation               |
| `/exit`    | Quit the chatbot                       |

## Configuration

Optional variables in `.env`:

| Variable             | Default       |
| -------------------- | ------------- |
| `OPENAI_MODEL`       | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | `0.7`         |
| `OPENAI_MAX_RETRIES` | `2`           |

## Prompting technique: few-shot

The support assistant uses **few-shot prompting**: the prompt includes a few example questions with their ideal JSON answers before the real question.

**Why few-shot**

| Need | How few-shot helps |
| ---- | ------------------ |
| Useful `confidence` | Without examples, the ambiguous question `"my order doesnt work"` got `confidence: 0.8`. Examples teach the model to lower it for vague questions. |
| Right `actions` | Examples show which catalog actions fit each kind of question. |
| Stable JSON contract | Examples show the exact answer shape. |
| Low cost and latency | One API call. Examples only add input tokens, the cheapest kind. |

**Why not the others**

| Technique | Reason it was not chosen |
| --------- | ------------------------ |
| Zero-shot | Current baseline. Poor confidence calibration on ambiguous questions. |
| Chain-of-thought | Adds output tokens (the expensive ones) and latency, and needs an extra `reasoning` field outside the contract. |
| Self-consistency | Needs N calls per question, so N times the cost and latency. |

**Trade-off:** examples are sent with every request, which increases input tokens per query.

See [docs/prompting-techniques.md](docs/prompting-techniques.md) for the full comparison.

## Project structure

```
src/chatbot/
├── main.py      # Chat loop
├── config.py    # Settings loaded from .env
├── client.py    # OpenAI calls
├── models.py    # Message model
├── commands.py  # Available commands
└── ui.py        # Terminal output with Rich
```
