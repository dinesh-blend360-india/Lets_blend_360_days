# Phase 6 failure analysis

## Execution status

The required Phase 5 command was attempted from `ai_engineering/7_rag`:

```powershell
python -m pytest .\tests -q
```

It did not reach test collection because PowerShell reported that `python` was
not recognized. No usable `python`, `py`, or `ollama` command is currently
available in this workspace. The `7_rag/outputs/` directory also contains no
Phase 5 results JSON to review.

Therefore, no actual Phase 5 case can truthfully be classified as a retrieval,
context, generation, or citation failure. This is an environment/execution
prerequisite failure that occurs before the RAG pipeline runs.

## Evidence reviewed

The real Day 06 structure-aware index is present at:

```text
../6_embedding_and_retrival/outputs/embeddings/employee_policy_md_structure/
```

Its manifest records BGE-small-en-v1.5, 384-dimensional vectors, query
instruction enabled, and 11 indexed chunks. The existing Day 06 receipt search
result records:

| Query | Chunk ID | Rank | Similarity |
|---|---|---:|---:|
| When is a receipt required? | `chunk_5762afc8dde264e56dd` | 1 | 0.8018798232078552 |

The known evidence is therefore sufficient to inspect retrieval once a working
Python environment is restored. No new retrieval, context, generation, or
citation output was fabricated during this phase.

## Representative failure

- Test/query ID: Phase 5 suite execution
- Expected behavior: collect and run the mocked tests, then write
  `outputs/phase5_rag_test_results.json`.
- Actual behavior: the shell could not locate `python`; no tests ran.
- Retrieved IDs/ranks/scores: not produced by this run. The prior saved Day 06
  receipt result is recorded above for reference only.
- Context excerpt: not produced by this run.
- Primary failure stage: environment prerequisite, before the four RAG stages.
- Evidence supporting diagnosis: the exact PowerShell command returned
  `python : The term 'python' is not recognized...`.
- Proposed fix: install or repair Python, create/repair the project virtual
  environment, install `..\requirements.txt`, then rerun the documented test
  and Phase 5 runner commands.

## Improvement decision

No retrieval, context, generation, or citation improvement was selected. The
test results do not provide evidence for one, and changing the prompt or
retrieval settings now would be speculative. There is no before/after
implementation comparison because no implementation change was justified.

## Required next run

```powershell
cd C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\7_rag
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements.txt
python -m pytest .\tests -q
python -m rag.phase5_runner
Get-Content .\outputs\phase5_rag_test_results.json
```

If Ollama and the configured model are available, run the optional integration
test only after the mocked suite passes:

```powershell
$env:RUN_RAG_INTEGRATION = "1"
python -m pytest .\tests -m integration -q
```
