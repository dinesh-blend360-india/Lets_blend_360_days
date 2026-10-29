# Day 16 setup

Open PowerShell in:

```text
C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\16_observability
```

## Dependencies

Everything Day 16 needs is already in the shared requirements file. From the
repository root:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
```

Throughout this file `$py` is the shared interpreter:

```powershell
$py = "..\..\venv\Scripts\python.exe"
```

To run Day 16 in isolation instead, `requirements.txt` here is the minimal
subset.

## Nothing else is required

Tracing writes to local JSONL files by default. **No LangSmith account, no API
key and no network are needed** for any command in this folder, including the
full test suite. A live Ollama model is needed only for the two live commands
(`obs.run_live_traced`, and `obs.make_evidence --model ...`).

## Verify

```powershell
& $py -m pytest -q
```

Expect **77 passed**. These use Day 15's scripted model and Day 10's mock
knowledge backend, so no model is contacted.

Then one traced run:

```powershell
& $py -m obs.run_traced --case D15-01 --show-trace
```

You should see a five-step tree: `assistant_request` → `llm_call (1)` →
`lookup_internal_knowledge` → `retrieve_policies` → `llm_call (2)`.

## Optional: LangSmith

Tracing is strictly better with a LangSmith project, but it is optional. Copy
`.env.example` to `../.env` (the shared file, which is git-ignored) and set:

```ini
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=day16-observability
```

With `LANGSMITH_TRACING=true` **and** a key present, runs are posted to that
project *in addition* to the local files. If either is missing, or the
`langsmith` package is not installed, the tracer silently stays on the local
backend — a tracing outage must not take the assistant down. Check which backend
is in use:

```powershell
& $py -c "from obs.tracing import Tracer; print(Tracer().backend)"
```

`local` or `langsmith+local`.

**Never commit a key.** `.env` is git-ignored; `.env.example` holds no real
values. Do not create public share links for traces containing data.

## Faults

All five are off unless asked for. Set one at a time:

```powershell
& $py -m obs.run_traced --case D15-01 --fault slow_tool --show-trace
```

or via the environment (`--fault` wins if both are set):

```powershell
$env:FAULT = "flaky_tool"
& $py -m obs.run_traced --case D15-01
$env:FAULT = ""        # switch off again
```

| Flag | Effect |
|---|---|
| `slow_tool` | 3 s delay inside the lookup tool |
| `flaky_tool` | First 2 lookup calls time out, then succeed |
| `mcp_error` | Lookup returns an MCP transport error |
| `bad_retrieval` | Lookup succeeds but returns no documents |
| `prompt_bloat` | The whole mock corpus is appended to the system prompt |

`slow_tool` makes a run take 3 s by design — that is the fault working, not a
hang.

## Reproduce the before/after

```powershell
& $py -m obs.run_traced --all --fault flaky_tool --retry 0 --out outputs/before.jsonl
& $py -m obs.run_traced --all --fault flaky_tool --retry 2 --out outputs/after.jsonl
& $py -m obs.compare_runs outputs/before.jsonl outputs/after.jsonl
```

Expect `fixed=8  regressed=0`. The committed copies are in `evidence/`; writing
to `outputs/` keeps your run separate from them.

## Regenerate the committed evidence

```powershell
& $py -m obs.make_evidence                      # scripted traces only
& $py -m obs.make_evidence --model llama3.2:3b  # also the two live traces
```

The live traces vary between runs: `llama3.2:3b` picks a different wrong tool on
different runs. The note at the top of each `.txt` is written from the observed
run, so it always matches the trace beside it.

## Troubleshooting

- `ModuleNotFoundError: obs` — run module commands from *this* directory
  (`python -m obs.run_traced`), not from `obs/`.
- `ModuleNotFoundError: src.assistant` — Day 10 could not be found. This folder
  must stay inside `ai_engineering/` next to `10_tool_calling/`.
- A run takes 3 s — `FAULT=slow_tool` is still set in your shell.
- `Unknown FAULT` — check the spelling against the table above.
- Live run times out — `llama3.2:3b` is much faster than `qwen3:4b` here; raise
  `--timeout` if needed.
