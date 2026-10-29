# Day 16 — AI Observability and Debugging

Day 15 said *which* cases fail. This day makes it possible to see *why*: every
request produces one trace, a tree of typed steps with inputs, outputs, timings,
errors and metadata, and the traces are used to diagnose two problems and fix
one, proven against the Day 15 suite.

Day 10 is **not modified**. `ControlledAssistant` already accepts an injected
model and registry, so instrumentation is added by composition. Days 10, 11, 14
and 15 behave exactly as before, which is also what makes the before/after
comparison fair — it is the same application, same cases, same checks.

## Challenge output

```text
16_observability/
├── obs/
│   ├── tracing.py          nested-run tracer; local JSONL backend, optional LangSmith
│   ├── masking.py          masking rules, applied at the tracer boundary
│   ├── faults.py           the five fault flags, all off by default
│   ├── instrumented.py     TracedModelClient / TracedToolRegistry + the retry fix
│   ├── run_traced.py       run Day 15 cases scripted, with tracing
│   ├── run_live_traced.py  run Day 15 cases against a live Ollama model
│   ├── compare_runs.py     before/after by case ID
│   └── make_evidence.py    regenerate everything under evidence/
├── evidence/               committed results and trace exports (see below)
├── outputs/traces/         working traces from local runs (git-ignored)
└── tests/                  77 tests, no model or network needed
```

Run it (from this directory, with the shared venv):

```powershell
$py = "..\..\venv\Scripts\python.exe"

& $py -m pytest -q                                        # 77 tests

# One case, with the trace printed as a tree
& $py -m obs.run_traced --case D15-01 --show-trace

# Each deliberate fault (one at a time; all off by default)
& $py -m obs.run_traced --case D15-01 --fault slow_tool     --show-trace
& $py -m obs.run_traced --case D15-01 --fault flaky_tool    --show-trace
& $py -m obs.run_traced --case D15-01 --fault mcp_error     --show-trace
& $py -m obs.run_traced --case D15-01 --fault bad_retrieval --show-trace
& $py -m obs.run_traced --case D15-01 --fault prompt_bloat  --show-trace

# The data case: personal data in, placeholders in the trace
& $py -m obs.run_traced --privacy-case --show-trace

# The fix, before and after, across the whole suite
& $py -m obs.run_traced --all --fault flaky_tool --retry 0 --out outputs/before.jsonl
& $py -m obs.run_traced --all --fault flaky_tool --retry 2 --out outputs/after.jsonl
& $py -m obs.compare_runs outputs/before.jsonl outputs/after.jsonl

# Live model (needed only for the quality diagnosis)
& $py -m obs.run_live_traced --model llama3.2:3b --case D15-03 --prompt-version v1 --show-trace
```

Faults can also be set with `FAULT=slow_tool` in the environment; `--fault`
overrides it. With no flag, the assistant behaves normally.

## Approach

**Steps traced.** Four run types, matching LangSmith's vocabulary so the local
records and a LangSmith project describe the same tree:

| Step | Type | Why it earns a run |
|---|---|---|
| `assistant_request` | `chain` | The whole request; carries the case ID and the totals |
| `llm_call (n)` | `llm` | The tool decision lives here; numbered so round 1 and 2 are distinguishable |
| `<tool_name>` | `tool` | One run per attempt, so retries are visible rather than collapsed |
| `retrieve_policies` | `retriever` | Nested under the lookup tool, so "what came back" is readable without opening the tool payload |

Deliberately *not* traced: argument validation, JSON parsing, and the
confirmation prompt. They are cheap, they never fail in a way the surrounding
tool run does not already show, and a run for each would triple the step count
for no diagnostic gain.

**Metadata on every run:** `case_id` (on the root), `model`, `prompt_version`,
`knowledge_backend`, `retry_attempts`, and `fault`. Tool runs add `attempt`;
LLM runs add `approx_input_tokens` and `message_count`.

**Finding a failing trace** is therefore: filter by `case_id`, then read down
the tree. `prompt_version` and `fault` exist so a comparison cannot silently mix
two configurations — the thing that makes most before/after claims worthless.

## Decisions

1. **Instrument by composition, not by editing Day 10.** Days 10, 11, 14 and 15
   all depend on that package. Wrapping the two injected interfaces gets a full
   trace while leaving shared behaviour untouched, and lets a test assert that a
   traced run returns the identical answer to an untraced one.
2. **Mask at the tracer boundary, not at the edges.** `start_run` and `end_run`
   mask before anything is stored on a run, so no unmasked payload is ever held
   in memory, written to a file, or sent to LangSmith. Masking the UI instead
   would still export the raw value.
3. **A tool returning `ok: false` is recorded as an errored step.** Day 10
   returns failures as values rather than raising. Without this translation a
   failed tool looks identical to a successful one in the tree, which is the
   exact failure mode F16-03 is about.
4. **Local file backend is the default; LangSmith is optional.** The tracer
   needs no account to be useful, and a tracing outage must never take the
   assistant down — the LangSmith client is best-effort and swallows its own
   errors.

## Trade-offs

**Masked inputs vs full inputs.** Full payloads debug faster: you can see the
exact text the model received. Masked payloads lose that, and a masking rule can
over-match — which happened here, see Failures. We mask, because the traces
would otherwise hold employee IDs and email addresses for anyone with project
access, and a debugging convenience does not justify that.

**Every request vs sampled.** We trace every request. At this scale that is
affordable (see Telemetry decision) and a sampled trace is worthless precisely
when you need it, because the failure you want is the one that was not sampled.
Above roughly 10k requests/day the arithmetic reverses: sample successes, keep
every error and every case run from the eval suite.

**One run per tool attempt vs one run per logical call.** Per-attempt is noisier
— three runs where the app made "one" call. It is what makes a retry storm
visible at a glance, so the noise is the point.

## Diagnoses

### 1. Quality — T16-01 / D15-03, unnecessary tool call

| Field | Value |
|---|---|
| Case | D15-03, "What can this assistant do?" — expects no tool call |
| Symptom from eval | `tool_selection: false` (Day 15 live smoke recorded the same) |
| Step where it went wrong | `llm_call (1)` |
| Evidence | Its output is a tool call, not text: `create_service_request{title: "assistant capabilities"}`. The step before it is clean, and the tool run then errors. Across runs this model also picks `lookup_internal_knowledge` with a non-integer `top_k` — the wrong tool varies, the wrong *decision point* does not. |
| Root cause | The model treats a capability question as actionable. Retrieval is uninvolved, so this is not a retrieval problem; the decision is made entirely inside the first LLM call. |
| Trace | [`evidence/traces/T16-01_D15-03_live_v1_shipped_prompt.txt`](evidence/traces/T16-01_D15-03_live_v1_shipped_prompt.txt) |

Reading the timings also answers "where does the time go": in one recorded run,
`llm_call (1)` took 13.4 s and `llm_call (2)` 21.4 s of a 34.9 s total, while
the tool itself took 1.3 ms. The unnecessary tool call costs a whole extra LLM
round-trip, not the tool's own time.

### 2. Error and latency — F16-02 / flaky_tool, no retry

| Field | Value |
|---|---|
| Case | D15-01 with `FAULT=flaky_tool` (first two tool calls time out, then succeed) |
| Symptom from eval | `source_citation: false` |
| Step where it went wrong | The single `lookup_internal_knowledge` run |
| Evidence | One tool run, errored with `TOOL_TIMEOUT`, 50.8 ms of a 50.8 ms total. `llm_call (2)` then answers from an error payload, with no citation and no mention of the failure. |
| Root cause | The application has **no retry at all**. A transient timeout becomes a permanent, user-visible wrong answer, and the user is never told the lookup failed. |
| Traces | [before](evidence/traces/F16-02_flaky_tool_D15-01_before_retry0.txt) · [after](evidence/traces/F16-02_flaky_tool_D15-01_after_retry2.txt) |

## Fix and re-evaluation

**What changed:** bounded retry for transient tool failures, in
`TracedToolRegistry.execute`. Only `TOOL_TIMEOUT` and `MCP_TRANSPORT_ERROR` are
retried; a validation error or permission denial is deterministic, so retrying
it would only burn time. The bound is 2 retries — unbounded retry turns a dead
dependency into a hang. Each attempt is its own run.

This is the *only* change. The retry sits in the Day 16 layer rather than Day
10's registry because that component is shared by four days; in a real codebase
it belongs beside the tool execution.

**Before vs after** — same suite, same 22 cases, same checks, same
`FAULT=flaky_tool`, only `--retry` differs:

```
compared=22  fixed=8  regressed=0  changed=0  still-failing=0  passing-throughout=14
```

| Case | Before failed | After failed | ms before | ms after | steps |
|---|---|---|---|---|---|
| D15-01 | `source_citation` | — | 50.8 | 105.7 | 4 → 7 |
| D15-02 | `source_citation` | — | 102.1 | 142.5 | 6 → 10 |
| D15-08 | `source_citation` | — | 51.4 | 105.8 | 4 → 7 |
| D15-09 | `source_citation` | — | 51.8 | 105.6 | 4 → 7 |
| D15-16 | `source_citation` | — | 51.2 | 106.1 | 4 → 7 |
| D15-L04 | `source_citation` | — | 51.4 | 122.9 | 4 → 7 |
| D15-L05 | `source_citation` | — | 51.3 | 105.7 | 4 → 7 |
| D15-L06 | `source_citation` | — | 102.9 | 141.9 | 6 → 10 |

The other 14 cases passed before and after. **No case got worse.**

**The cost, stated plainly:** latency roughly doubles on any case that hits the
fault (≈51 ms → ≈106 ms here, dominated by the injected failure delay), and the
suite's total step count rises from 78 to 107. That is the price of recovering 8
cases; it is paid only when a tool actually fails.

**The fix is inert when nothing is failing.** Re-running the suite with no fault
and `--retry 2` gives 22/22 passing and zero changed cases — see
`evidence/before_nofault_retry0.jsonl` vs `evidence/after_nofault_retry2.jsonl`.
Two tests assert both comparisons so this cannot rot.

## Failures

**The prompt fix was tested and rejected.** The first hypothesis for D15-03 was
that the shipped prompt's "use lookup evidence for knowledge claims" nudged the
model toward a tool. `PROMPT_VERSIONS["v2"]` rewords it to scope tool use
explicitly ("answer directly, with no tool call, when the user asks what you can
do"). With `llama3.2:3b` it **did not work** — the model still called
`create_service_request`. A sharper variant with numbered rules and an explicit
"never call it to describe yourself" did not work either. Evidence:
[`T16-01_D15-03_live_v2_rejected_fix.txt`](evidence/traces/T16-01_D15-03_live_v2_rejected_fix.txt).
v1 and v2 are both kept so the rejected hypothesis stays reproducible.

**What the traces could not explain.** The trace shows *that* `llm_call (1)`
chose a tool and what it received, but not *why*. Distinguishing "the prompt
caused it" from "this 3B model is weak at tool choice" needs evidence a trace
does not contain: the same case against a larger model, and against a pared-down
tool schema. That is the next experiment, and it is why this was diagnosed but
not fixed.

**Two further gaps.** The traces cannot tell whether an answer faithfully
summarises the retrieved text — F16-04 produces a wrong answer with *zero*
errored steps, detectable only because the retriever run reports
`document_count: 0`. And `approx_input_tokens` is a 4-chars-per-token estimate,
not a billing figure; real cost work needs the model's own token counts.

## Telemetry decision

**Collected:** step name, type, parent, trace ID, start/end time, duration,
masked inputs and outputs, error, and the metadata listed under Approach.

**Masked in code, before export:** email addresses, employee IDs (`E1023`),
Indian mobile numbers, and API-key-shaped strings. Keys named `api_key`,
`authorization`, `password`, `token` or `secret` have their values **dropped**
outright rather than pattern-matched — a secret does not become safe by being
shortened.

**Dropped entirely:** nothing is collected that is not listed above. No raw user
identity, no auth headers.

**Volume.** One eval run over the 22 cases produces **22 traces / 89 runs**
normally, 107 runs with retries active. That is about 0.2% of the LangSmith
Developer plan's 5,000 free traces per month per eval run, so roughly 220 full
eval runs per month fit inside the free tier. Tracing every request is
affordable at this scale; it would not be at 1,000 user requests/day, where the
sampling split under Trade-offs applies.

**Who should see traces, and for how long.** Traces contain the user's question
verbatim, masked but not anonymous — a policy question can identify its asker by
context. They should be visible to the engineers debugging this assistant, not
to the whole organisation, and retained ~30 days: long enough to investigate a
reported failure, short enough that an old project is not a standing liability.
No public share links for traces containing data.

## FDE Lens

*What telemetry is useful enough to collect without creating a privacy or cost
problem — for this assistant and its users?*

The step tree, timings, errors and tool names carry nearly all the diagnostic
value and almost none of the privacy risk: they are about the *application*, not
the person. The expensive and sensitive part is the payloads — the question, the
retrieved text, the answer. For this helpdesk assistant that asymmetry suggests
keeping full structure and timing for every request indefinitely, and payloads
masked and short-lived.

The customer question to settle before this goes anywhere real is who the users
are. Employees asking HR questions have a reasonable expectation that "my
manager won't read what I asked the helpdesk" — and a trace project where
anyone can read the inputs quietly breaks that, whether or not the IDs are
masked. That is a policy decision for the customer, not a default for an
engineer to pick.

## Reflection

With one more hour: feed Day 15's check results back onto the matching runs as
feedback, so a failing score and its trace sit together instead of in two files
that have to be joined by case ID by hand. Right now the diagnosis loop is
"read the comparison, find the case ID, open the trace" — three steps that
should be one. It is the cheapest remaining change that makes the next
diagnosis faster, which is the whole point of the day.

## Evidence index

| File | What it shows |
|---|---|
| `evidence/before_flaky_retry0.jsonl` | Full suite, `FAULT=flaky_tool`, no retry — 8 failures |
| `evidence/after_flaky_retry2.jsonl` | Same, with the fix — 0 failures |
| `evidence/before_nofault_retry0.jsonl` / `after_nofault_retry2.jsonl` | The fix is inert with no fault |
| `evidence/traces/F16-01_slow_tool_D15-01.*` | Latency: the tool run dominates |
| `evidence/traces/F16-02_flaky_tool_D15-01_before_retry0.*` | Error: one errored tool run, no retry |
| `evidence/traces/F16-02_flaky_tool_D15-01_after_retry2.*` | The retries, two errored then success |
| `evidence/traces/F16-02_flaky_tool_D15-02_before_retry0.*` | A second failing case: two lookups, both affected |
| `evidence/traces/F16-02_flaky_tool_D15-16_before_retry0.*` | A third failing case: the Hinglish variant |
| `evidence/traces/F16-03_mcp_error_D15-01.*` | Transport error on the tool run |
| `evidence/traces/F16-04_bad_retrieval_D15-01.*` | Wrong answer with **no** errored step |
| `evidence/traces/F16-05_prompt_bloat_D15-01.*` | Input-token estimate rises |
| `evidence/traces/F16-06_masking_personal_data.*` | Employee ID and email as placeholders |
| `evidence/traces/T16-01_D15-03_live_v1_shipped_prompt.*` | The quality failure |
| `evidence/traces/T16-01_D15-03_live_v2_rejected_fix.*` | The rejected prompt hypothesis |

Each `.jsonl` is the raw trace; the `.txt` beside it is the same trace as a tree
with a summary. Regenerate everything with:

```powershell
& $py -m obs.make_evidence --model llama3.2:3b
```

Scenario IDs follow the Day 16 Common Mixed Test Cases. The scenarios there
assume leave-balance and ticket-status tools; this assistant has a policy lookup
and a service-request tool, so the closest equivalents are used and the IDs
kept, as that document instructs.
