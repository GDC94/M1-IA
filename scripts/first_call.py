"""Minimal smoke test: one request to the OpenAI Responses API."""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
)

print(response.choices[0].message.content)


print("Uso de tokens: ", "de entrada", response.usage.prompt_tokens, "de salida", response.usage.completion_tokens, "total", response.usage.total_tokens)

cost_input = (response.usage.prompt_tokens / 1_000_000) * 0.15
cost_output = (response.usage.completion_tokens / 1_000_000) * 0.60
total_cost = cost_input + cost_output

print(f"Costo total: {total_cost:.6f} USD")