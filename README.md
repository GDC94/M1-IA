# Support Assistant

A command-line assistant for customer support agents. It receives a customer question and returns
a JSON answer with a confidence score, recommended actions, and per-query metrics
(tokens, latency, and estimated cost). Answers are written in Spanish.
Built with the OpenAI API, Pydantic, python-dotenv, and Rich.

📄 **Technical report (Spanish):** [docs/REPORT.md](docs/REPORT.md)

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
uv run support "me cobraron dos veces este mes"
```

Output (stdout, exit code `0`):

```json
{
  "answer": "Lamentamos la confusión. Vamos a verificar los cobros en tu cuenta para aclarar la situación.",
  "confidence": 0.8,
  "actions": ["check_payment_history"],
  "metrics": {
    "prompt_tokens": 585,
    "completion_tokens": 39,
    "total_tokens": 624,
    "latency_ms": 1235.4,
    "estimated_cost_usd": 0.00011115
  }
}
```

In a terminal the JSON is colored with Rich. When piped to another program, plain JSON is printed.

### Contract

| Field | Type | Description |
| ----- | ---- | ----------- |
| `answer` | string | Concise reply the agent can send (Spanish, max 3 sentences) |
| `confidence` | number `0`–`1` | Model's self-estimated confidence |
| `actions` | array | Values from a closed catalog: `check_order_status`, `check_payment_history`, `refund_order`, `reset_password`, `update_account_details`, `request_more_information`, `share_help_article`, `escalate_to_human` |
| `metrics` | object | `prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`, `estimated_cost_usd` |

### Errors

Errors are printed as JSON on stderr with exit code `1`:

```json
{"error": "rate_limit", "message": "Rate limit exceeded. Please try again later."}
```

Error codes: `invalid_input`, `invalid_config`, `authentication_error`, `rate_limit`, `connection_error`,
`api_error`, `no_answer`, `pricing_error`.

## Support rules

After the model answers, `decision.py` applies deterministic rules in code:

- If the question contains fraud or legal terms (`fraude`, `estafa`, `denuncia`, `abogado`, `demanda`, `legal`...), `escalate_to_human` is added.
- If `confidence` is below `0.5`, `request_more_information` is added.

Rules only add actions; they never remove the model's actions or change `confidence`.

## Metrics log

Every successful run appends one line to `logs/metrics.jsonl` (the customer question is not stored):

```json
{"prompt_tokens":585,"completion_tokens":39,"total_tokens":624,"latency_ms":1235.4,"estimated_cost_usd":0.00011115,"timestamp":"2026-09-13T23:26:15Z","model":"gpt-4o-mini"}
```

## Configuration

Optional variables in `.env`:

| Variable                   | Default       |
| -------------------------- | ------------- |
| `OPENAI_MODEL`             | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE`       | `0.2`         |
| `OPENAI_MAX_OUTPUT_TOKENS` | `500`         |
| `OPENAI_MAX_RETRIES`       | `2`           |

The model must have a price in `src/support_assistant/pricing.py`.

## Prompting technique: few-shot

The system prompt defines a confidence scale and rules, followed by **four example questions** with their
ideal JSON answers (clear, ambiguous, missing details, fraud threat).

**Why few-shot**

- One API call per question. Examples only add input tokens, the cheapest kind.
- Examples make actions more precise and answers shorter.
- Chain-of-thought adds expensive output tokens and a `reasoning` field outside the contract.
- Self-consistency needs N calls per question, so N times the cost and latency.

**Measured effect** (6 questions × 3 runs, `gpt-4o-mini`):

| Per query | Zero-shot | Few-shot |
| --------- | --------- | -------- |
| Prompt tokens | 344 | 586 |
| Completion tokens | 54 | 44 |
| Cost per 1,000 queries | $0.084 | $0.114 (+36%) |

Most of the confidence calibration comes from the explicit scale in the system prompt; the examples mainly
remove unnecessary actions (e.g. zero-shot added `request_more_information` to "¿cómo cambio mi contraseña?").

Details: [docs/REPORT.md](docs/REPORT.md) · Technique comparison: [docs/prompting-techniques.md](docs/prompting-techniques.md)

## Tests

```bash
uv run pytest
```

41 tests with a fake language model (no network, no cost): JSON contract, cost calculation, metrics mapping,
error handling, prompt structure, decision rules, metrics log, and CLI error codes.

## Project structure

```
src/support_assistant/
├── cli.py          # Entry point: question in, JSON out
├── support.py      # ask_support: builds the prompt, calls the model, computes metrics
├── prompts.py      # Few-shot system prompt and examples
├── llm.py          # LanguageModel interface and OpenAI adapter (responses.parse)
├── decision.py     # Deterministic rules applied after the model
├── models.py       # JSON contract (SupportAnswer, Metrics, SupportResponse)
├── pricing.py      # Token prices and cost estimation
├── metrics_log.py  # Per-run metrics log (JSON Lines)
├── config.py       # Settings loaded from .env
├── client.py       # Builds the OpenAI adapter
└── ui.py           # Rich output for terminals, plain JSON for pipes
tests/              # pytest suite
docs/
├── REPORT.md                 # Technical report (Spanish)
└── prompting-techniques.md   # Prompting techniques theory (Spanish)
```
