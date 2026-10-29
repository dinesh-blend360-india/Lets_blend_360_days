# Day 03 — Structured output: making a model's answer usable by code

| | |
|---|---|
| **Folder** | `03_structured_output/` — `reliability.py`, `structured_validation.py`, `test_reliability.py` |
| **Commands** | App: `& $py -m streamlit run 03_structured_output\structured_validation.py` · Tests: `& $py -m pytest -q` |
| **Needs** | App: Ollama + a model. Tests: nothing (they use a fake client). |
| **Time** | 1–2 hours |
| **Depends on** | Day 02 helps (same A/B/C framing), but nothing is required. |

---

## 1. What you are learning

Free text is fine for a person and useless for a program. If code needs to
*act* on a model's answer — show it, store it, route on it — the answer must
have a **fixed shape that is checked before it is trusted**.

This day builds that discipline in five small ideas:

1. **A contract.** `AIResponse` (a Pydantic model) says an answer is exactly
   `{"status": "success" | "needs_clarification", "answer": "<non-empty string>"}`
   and nothing else (`extra = "forbid"`).
2. **Asking the model for it.** Ollama's `format=<JSON schema>` option makes the
   model constrain its output to that schema.
3. **Never trusting it anyway.** Even with a schema requested, the output is
   parsed and validated again, because a model can still return broken or
   unexpected data.
4. **Bounded retry with feedback.** If validation fails, retry **once** and tell
   the model what was wrong. Never loop forever (`MAX_ATTEMPTS = 2`).
5. **A safe fallback.** After the attempts are used up, return a clear failure
   instead of a half-parsed answer, and keep technical detail for developers.

Related engineering judgement: **which failures are worth retrying?** A timeout,
a network blip, HTTP 429 or a 5xx are *transient* — retry. A "model not found"
or a validation error that repeats are *permanent* or model-quality problems —
don't hammer them.

## 2. Setup

Same as Day 01/02. For the app, choose a quick model:

```powershell
$env:OLLAMA_MODEL = "llama3.2:3b"
```

For the tests you need only the shared environment.

## 3. Run

### Tests first (no model needed)

```powershell
Set-Location "$ai\03_structured_output"
& $py -m pytest -q
& $py -m pytest -q -s        # -s also prints each test's "PASS: …" sentence
```

### The app

```powershell
Set-Location $ai
& $py -m streamlit run 03_structured_output\structured_validation.py
```

You get a question box, a **Relevant Context** box and a single **Run Version C**
button. (Buttons for Versions A and B are commented out in this app; every
version shares the same structured-output contract.) The result appears in an
expandable **Validated JSON output** panel, then a green message with the answer.

## 4. What to test

**In the app**

- [ ] A clear question: `What is the capital of France?` → a `success` response.
- [ ] A vague one: `How many days do I get?` → a `needs_clarification` response
  that asks you what you mean.
- [ ] A question with supplied context (paste a policy line in the box).
- [ ] Empty question → a warning, no model call.
- [ ] Stop Ollama, run again → after two attempts, a red "The AI could not
  produce a valid response" plus a *Developer diagnostics* box holding the real
  error.
- [ ] Re-run the same question several times. With `temperature = 0` the shape
  should be stable; the wording usually is too.

**Break it on purpose.** Inside `client_build` in `structured_validation.py`,
right after `raw_output = response.message.content or ""`, there are four
commented lines. Uncomment **one at a time** and run a question:

| Uncomment this `raw_output = …` | You are simulating | Expected |
|---|---|---|
| `'{"status": "success",'` | Truncated / malformed JSON | Fails, retries, fails again → fallback |
| `'{"status": "success"}'` | A missing required field | Same |
| `'{"status": "success", "answer": 123}'` | Wrong data type | Same |
| `'Here is your answer: {"status":"success","answer":"Hello"}'` | Extra chatter around the JSON | Same (parsing is strict) |

Because the injected value is *the same on both attempts*, retry cannot recover.
That is the point: now ask why the tests include a case where the **second**
attempt succeeds.

**In the tests** — read them, they are the specification. The 13 cases cover:
valid output; malformed JSON; missing field; wrong type; a status value outside
the allowed list; an unexpected extra field; text around the JSON; a
clarification response; retry that **recovers**; retry **exhausted → fallback**;
a timeout that recovers; repeated timeouts → fallback; and "the attempt limit is
never exceeded".

- [ ] Change `MAX_ATTEMPTS` to 3 and see which tests notice.
- [ ] Add your own: a response with `"status": "SUCCESS"` (capitals). Should it pass?

## 5. What to expect

**Tests:** `13 passed, 1 warning` in well under a second. The warning is
`PydanticDeprecatedSince20: Support for class-based config is deprecated` — see
section 8.

**Live results** (observed with `llama3.2:3b`, `temperature 0`):

| Question | Result |
|---|---|
| `What is the capital of France?` | `{'status': 'success', 'answer': 'Paris'}` (~10 s including model load) |
| `How many days do I get?` | `{'status': 'needs_clarification', 'answer': "I'm not sure which type of leave or benefit you're referring to. Could you please provide more context or clarify which days you're asking about?"}` (~5 s) |
| Ollama unreachable | `None` plus the last error, after **two attempts**. In my test (an address that never answers, 2-second timeout) that was `ConnectTimeout: timed out` after ~8 s. In the app the client timeout is 60 s, so a *hung* server can take up to 60 s per attempt; a server that is simply stopped refuses the connection at once and falls back quickly. |

The model reliably produced valid JSON here because the schema was passed to
Ollama. That is not a guarantee — hence the validation layer.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| "The AI could not produce a valid response" immediately | Ollama down, or model missing | Developer diagnostics shows the real error; start Ollama / `ollama pull` |
| `ollama.ResponseError … model not found` is **not** retried | Correct behaviour: 4xx errors are permanent | Fix the model name |
| Test run says `PydanticDeprecatedSince20` | Harmless warning | See section 8 |
| App behaves differently from the tests | The app re-implements the loop inline; `reliability.py` is the tested copy | See section 8 |
| Model returns prose instead of JSON | Rare with `format=`; also what the injected failures simulate | The retry + fallback path handles it |

## 7. Learn more

- **Pydantic v2** documentation — models, `ConfigDict`, `field_validator`,
  `model_validate_json`. <https://docs.pydantic.dev>
- **JSON Schema** basics (types, enums, `required`, `additionalProperties`).
- **Structured outputs / constrained decoding** — how a model can be forced to
  emit valid JSON, and why it still can be semantically wrong.
- **Retry patterns:** exponential backoff, jitter, circuit breakers, idempotency
  (idempotency returns in Day 12).
- **Tool calling** (Day 10) is structured output with a different wrapper.
- Compare a Pydantic-validated approach with the `instructor` library or native
  provider "JSON mode".

## 8. What you might be missing

- **Valid ≠ correct.** A response can pass every check and still be wrong:
  `{"status": "success", "answer": "Lyon"}` is perfectly valid. Validation
  protects *code*, not *truth*. This distinction is the root of Days 08 and 15.
- **Two copies of the logic.** `reliability.py` is the clean, tested version.
  `structured_validation.py` repeats the same retry loop inline inside the
  Streamlit function, so the **tests do not exercise the app's own loop**. If
  you fix a bug in one, fix the other (or better: make the app call
  `generate_validated_response`).
- **The test file lives beside the code**, not in a `tests/` folder like Days
  04–16. `pytest` still finds it when you run it from this folder. Pointing
  pytest at the folder from elsewhere also works; just be consistent.
- **Deprecated Pydantic style.** `class Config: extra = "forbid"` is the v1
  idiom. The modern equivalent is `model_config = ConfigDict(extra="forbid")`.
  It works today but is slated for removal in Pydantic v3. A good small
  exercise.
- **`needs_clarification` is a design choice, not magic.** The model is *told*
  (in `CONTRACT_INSTRUCTIONS`) to use it when information is missing. It is
  only as good as that instruction.
- **Retrying a bad answer costs a full extra model call** — latency and, with a
  paid API, money. Two attempts is a deliberate bound. Measure before raising it.
- **What you do *not* get:** no logging of the failure to a file, no metric of
  how often retries happen, no alert. Day 16 adds the visibility this lacks.
- **Context window is still 2048** (`num_ctx`). A long context box could truncate
  your instructions *including the JSON contract* and cause invalid output.
- **Security:** nothing here sanitises user input. Never let a validated answer
  trigger an action without more checks (Day 10).

## 9. Where this leads

Day 04 builds an API where validation is the *front door*. Day 10 reuses the
same idea for tool arguments (a model proposes, the application validates before
executing). Day 15 builds checks around outputs like these.
