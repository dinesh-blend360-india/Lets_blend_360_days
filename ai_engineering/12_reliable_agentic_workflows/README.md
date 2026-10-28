# Day 12 Reliable Agentic Workflows

This lesson hardens the Day 11 leave demonstration with a deterministic workflow. The model may interpret a user's request, but eligibility and creation are decided by `workflow.py`. The workflow resolves a festival date, adds a bounded day offset, reads a trusted demo balance, checks already recorded leave, and asks for approval before writing a **simulated local** request.

The example from the training slides, “Can I take leave the day after Diwali? I have 2 days left,” is a **check** unless the user explicitly asks to create a request. The supplied “2 days” is untrusted; the workflow reads its configured balance. With fixture user E104, Day 12 calculates 2026-11-09 and finds exactly two days available.

## States and stopping

`received → validated → balance_checked → eligible` for a check. A create request passes through `approval_pending`, then ends as `created`, `declined`, `blocked`, or `failed`. Every run ends in one of those statuses and appends a JSONL audit record with the state trace and run ID.

The idempotency key uses employee ID, date, leave type, and duration. An exact retry returns the original request ID; a different request that overlaps recorded leave is blocked. Malformed records fail closed, and a failed audit append is reported in `audit_error` even when the simulated request was saved. A write uses a temporary file and atomic replacement. This local store is single-process teaching code; a customer system needs transactional storage or a lock for concurrent writers, real identity, HR approval policy, and a durable external audit service.

## Run and evidence

```powershell
python workflow.py --user E104 --festival Diwali --offset 1 --days 2
python workflow.py --user E104 --festival Diwali --offset 1 --days 2 --create
python -m pytest tests -q
```

The second command displays the exact proposal and writes only if you type `CONFIRM`. Local records and traces go under `outputs/`. Tests cover exact and insufficient balance, ten repeated decisions, idempotent retries, unknown data, a past date, declined approval, and a failed write. No real HR service is called.
