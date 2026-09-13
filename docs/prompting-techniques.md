# Técnicas de prompting

Un prompt es todo lo que el modelo lee antes de responder: instrucciones, ejemplos y la pregunta del usuario.
Una técnica de prompting es una forma de organizar esa entrada para obtener mejores respuestas.

## Comparación rápida

| Técnica | Idea | Llamadas a la API | Costo extra | Ideal para |
|---------|------|-------------------|-------------|------------|
| Zero-shot | Solo instrucciones | 1 | Ninguno | Tareas simples y conocidas |
| Few-shot | Instrucciones + ejemplos | 1 | Bajo (los ejemplos suman tokens de entrada) | Formato, tono y criterio consistentes |
| Chain-of-thought | Pedir al modelo que razone paso a paso | 1 | Medio (más tokens de salida, que son los más caros) | Lógica, matemática, problemas de varios pasos |
| Self-consistency | Preguntar N veces y elegir la respuesta más frecuente | N | Alto (N × costo y latencia) | Respuestas críticas donde la precisión importa más que el costo |

Dos herramientas relacionadas que no son técnicas por sí solas:

- **Role prompting**: "You are a support expert...". Define el tono y el contexto. Normalmente se combina con las demás.
- **Structured output**: obliga a respetar una forma de respuesta (por ejemplo, JSON). Controla la **forma**, no la **calidad** del contenido.

---

## 1. Zero-shot

El modelo recibe las instrucciones y la pregunta. Sin ejemplos.

```text
system: Reply with an answer, a confidence between 0 and 1, and recommended actions.
user:   my order doesnt work
```

| A favor | En contra |
|---------|-----------|
| El prompt más corto y económico | El modelo adivina qué es una "buena" respuesta |
| Fácil de escribir y modificar | Criterio inconsistente en casos límite |

**Observado en este proyecto:** la pregunta ambigua `"my order doesnt work"` obtuvo `confidence: 0.8`.
El modelo no tenía ninguna referencia de cómo luce una pregunta ambigua.

## 2. Few-shot

El modelo recibe las instrucciones más 2 a 5 ejemplos de pares entrada → salida ideales, y luego la pregunta real.
Imita el patrón.

```text
system:    Reply with an answer, a confidence between 0 and 1, and recommended actions.
user:      How do I change my password?
assistant: {"answer": "Go to Settings > Security > Change password.", "confidence": 0.95, "actions": ["reset_password", "share_help_article"]}
user:      It doesn't work
assistant: {"answer": "Could you tell me what is not working and what you tried?", "confidence": 0.3, "actions": ["request_more_information"]}
user:      my order doesnt work
```

| A favor | En contra |
|---------|-----------|
| Una sola llamada, costo extra bajo | Los ejemplos se envían en **cada** llamada |
| Enseña formato, tono y calibración | Ejemplos malos o muy parecidos enseñan malos hábitos |
| Fácil de explicar y mantener | Demasiados ejemplos pueden hacer que el modelo los copie |

**Cómo elegir los ejemplos:** cubrir situaciones distintas, no tres parecidas.

- [ ] Una pregunta clara → confianza alta
- [ ] Una pregunta ambigua → confianza baja + `request_more_information`
- [ ] Un caso delicado (cliente enojado, tema legal, cancelación) → `escalate_to_human`

## 3. Chain-of-thought (CoT)

Se le pide al modelo que razone antes de responder.

```text
system: First analyze the customer's problem step by step. Then give your final answer.
```

| A favor | En contra |
|---------|-----------|
| Mejor en lógica y problemas de varios pasos | Más tokens de salida → mayor costo y latencia |
| El razonamiento se puede inspeccionar | Con salida JSON, necesita un campo extra (por ejemplo, `reasoning`) que el contrato no pedía |

Nota: los modelos de razonamiento (por ejemplo, la serie o y la familia GPT-5) ya razonan internamente, por lo que pedir CoT explícito aporta menos con ellos.

## 4. Self-consistency

La misma pregunta se envía N veces (por ejemplo, 5) con una temperatura más alta. Gana la respuesta más frecuente.

```text
llamada 1 → refund_order
llamada 2 → refund_order
llamada 3 → escalate_to_human
llamada 4 → refund_order
llamada 5 → refund_order
resultado → refund_order (coincidencia: 4/5 = 0.8)
```

| A favor | En contra |
|---------|-----------|
| Respuestas más confiables | N veces el costo y la latencia |
| El nivel de coincidencia es una confianza **medida**, no autoestimada | Más código: llamadas en paralelo y lógica de votación |

---

## Elección para este proyecto: few-shot

| Requisito | Por qué encaja few-shot |
|-----------|-------------------------|
| Medir costo y latencia por consulta | Una llamada y pocos tokens extra. CoT y self-consistency empeoran ambos |
| Contrato JSON estable | Los ejemplos muestran la forma exacta del JSON y el uso del catálogo de acciones |
| `confidence` útil | Los ejemplos enseñan cuándo bajarla (preguntas ambiguas) |
| Acciones recomendadas | Los ejemplos muestran qué acciones corresponden a cada tipo de pregunta |

**Trade-off a tener en cuenta:** los ejemplos suman tokens de entrada a cada solicitud.
Medir la cantidad de tokens antes y después de agregarlos, y reportar la diferencia.

## Glosario

| Término | Significado |
|---------|-------------|
| Token | Fragmento de texto que el modelo lee o escribe (aproximadamente ¾ de una palabra en inglés) |
| Tokens de entrada (input / prompt) | Tokens enviados al modelo: instrucciones, ejemplos, pregunta |
| Tokens de salida (output / completion) | Tokens que genera el modelo. Suelen ser más caros que los de entrada |
| Temperatura | Cuánto azar usa el modelo al elegir palabras (0 = predecible) |
| Calibración | Qué tan bien coincide la confianza declarada con la precisión real |
