# Day 12 — Reliable agentic workflows: decisions that don't vary

| | |
|---|---|
| **Folder** | `12_reliable_agentic_workflows/` — `workflow.py`, `tests/`, `outputs/` |
| **Commands** | Check: `& $py workflow.py --user E104 --festival Diwali --offset 1 --days 2` · Create: add `--create` |
| **Needs** | **Nothing but Python.** No model, no Ollama, no internet. |
| **Time** | 1–1.5 hours |
| **Depends on** | Day 11 (same leave task — compare the two). |

---

## 1. What you are learning

Day 11 let a model *decide* what to do. It sometimes did the right thing and
sometimes skipped the tool call entirely. For anything with consequences —
leave, money, access — that is not acceptable. Day 12 rebuilds the **same task
with the decisions taken away from the model.**

> **A model may *interpret* a request. Code *decides* and *acts*.**

`workflow.py` is a small, explicit **state machine**:

```text
received → validated → balance_checked → eligible                      (a check)
                                       ↘ approval_pending → created | declined | failed
(any early step may end in: blocked | failed)
```

It teaches five engineering ideas:

1. **Deterministic decisions.** Eligibility is arithmetic on trusted data. Run it
   ten times, get the same answer ten times — and there is a test that does.
2. **Don't trust the user's numbers.** "I have 2 days left" is *ignored*. The
   workflow reads its own configured balance. Otherwise a user could authorise
   their own leave by claiming a balance.
3. **Check versus create.** Without `--create` nothing is ever written. Writing is
   a separate, explicit act.
4. **Approval of the exact proposal.** Before a write, the workflow shows the exact
   record and requires a typed `CONFIRM`.
5. **Idempotency.** The request ID is derived from the request itself (employee +
   date + type + duration). Submitting the same request twice yields the same ID
   and **no second record**. Overlapping *different* requests are blocked.

Plus **audit** (every run ends in a named status and appends a JSON line with its
state trace) and **fail-closed** behaviour (a corrupt store or a failed write is
reported, never reported as success).

## 2. Setup

Nothing. Check:

```powershell
Set-Location "$ai\12_reliable_agentic_workflows"
& $py -m pytest -q          # 12 passed
```

Demo data (hard-coded, **not real HR data**; defined in `DEFAULT_EMPLOYEES` / `DEFAULT_FESTIVALS`):

| Employee | Name | Balance |
|---|---|---|
| `E101` | Priya | 3 |
| `E102` | Rahul | 0 |
| `E103` | Anita | 5 |
| `E104` | Sam | 2 |

| Festival | Date |
|---|---|
| Diwali | 2026-11-08 |
| Dussehra | 2026-10-20 |
| Pongal | 2027-01-14 |

(Different from Day 11: here there are four employees and three festivals.)

## 3. Run

```powershell
# A CHECK: "Can Sam take leave the day after Diwali, for 2 days?"
& $py workflow.py --user E104 --festival Diwali --offset 1 --days 2

# CREATE a (simulated, local) request: you will be shown it and asked to type CONFIRM
& $py workflow.py --user E104 --festival Diwali --offset 1 --days 2 --create

& $py -m pytest -q
```

Options: `--user` (default `E104`), `--festival` (default `Diwali`), `--offset`
(days after the festival, 0–30), `--days` (leave length, 1–30), `--create`.

Output is one JSON object: `run_id`, `status`, `code`, `trace` (every state), and,
where relevant, `date`, `available`, `request_id`.

**Files** (all inside `outputs\`, git-ignored):

| File | Contents |
|---|---|
| `requests.json` | The simulated leave records you have created |
| `runs.jsonl` | The audit log: one line per run, including blocked and failed runs |

## 4. What to test

Run each of these and note `status` **and** `code`:

- [ ] **The slide example:** `--user E104 --festival Diwali --offset 1 --days 2`.
- [ ] **Not enough balance:** `--user E104 --days 3` (balance 2), then `--user E102`
  (balance 0).
- [ ] **Unknown user / festival:** `--user E999`, `--festival Holi`.
- [ ] **A past date:** `--festival Dussehra --offset 0`.
- [ ] **Out-of-range input:** `--offset 31`, `--days 0`.
- [ ] **Create → CONFIRM:** the happy path. Note the `request_id`.
- [ ] **Create → anything else** (type `no`): the proposal is shown, nothing is written.
  (Use a request you have **not** already created — see the gotcha below.)
- [ ] **Repeat the same create.** You get the *same* `request_id`, no second record.
- [ ] **An overlapping request:** after creating Nov 9–10, try `--days 1`
  (Nov 9) — different request, but it overlaps.
- [ ] **Use up the balance:** after Sam's two days are booked, try Pongal.
- [ ] **Read `runs.jsonl`** — every run above is in there, including the refusals.
- [ ] **Corrupt the store:** put a stray character in `outputs\requests.json`, then run a
  check. Expect `status: failed`, `code: STORE_READ_FAILED` and a trace of just
  `received > validated > failed` — a visible refusal, not a guess.
- [ ] **Delete `requests.json`** to reset your demo state.

Then compare with Day 11: run the *same intent* through `11_agents\main.py` several
times. How many different behaviours? Then run this ten times. How many?

## 5. What to expect

All of the following were observed, exactly, with today set to 2026-10-29.
Every **status/code** pair below is deterministic — it will not vary.

| What you ran | `status` | `code` | Notes |
|---|---|---|---|
| Check: Sam, Diwali +1, 2 days | `eligible` | `CHECK_ONLY` | `date: 2026-11-09`, `available: 2` |
| Check: Rahul (balance 0) | `blocked` | `INSUFFICIENT_BALANCE` | `available: 0` |
| Check: Sam wants 3 days | `blocked` | `INSUFFICIENT_BALANCE` | `available: 2` |
| Check: `E999` | `blocked` | `UNKNOWN_USER` | stops at step 2 |
| Check: festival `Holi` | `blocked` | `UNKNOWN_FESTIVAL` | Holi exists on Day 11, **not here** |
| Check: Dussehra, offset 0 | `blocked` | `PAST_DATE` | `date: 2026-10-20` |
| Check: offset 31 | `blocked` | `INVALID_OFFSET` | the limit is 30 |
| Create, CONFIRM | `created` | `SIMULATED_CREATED` | `request_id: LR-7ff5a81c39` |
| Create, identical retry | `created` | `ALREADY_CREATED` | **same** ID, no new record |
| Create, 1 day overlapping | `blocked` | `OVERLAPPING_LEAVE` | names the existing request |
| Create, later date, balance spent | `blocked` | `INSUFFICIENT_BALANCE` | `available: 0` |
| Create, user types something else | `declined` | `NOT_APPROVED` | nothing written |
| Create, approval handler throws | `failed` | `APPROVAL_HANDLER_FAILED` | no side effect |

The state `trace` tells you *where* a run stopped. For a successful create:

```text
received > validated > balance_checked > approval_pending > created
```

For an unknown user it is just `received > blocked`.

**`LR-7ff5a81c39` is not random.** It is the first 10 hex digits of the SHA-256 of
`E104|2026-11-09|annual|2` (employee, date, type, days) — so the same request
always gets the same ID. That
is how idempotency works here.

**Tests:** `12 passed` (under a second). They cover exact and insufficient
balance, ten repeated decisions, idempotent retries, unknown data, a past date,
declined approval, a failed write, a failed approval handler, overlap, and a
corrupt store.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `Type CONFIRM to record it:` and it waits | Working as designed | Type `CONFIRM` exactly (capitals) |
| No prompt appears; `code: ALREADY_CREATED` | This exact request was already created | See the gotcha below |
| `blocked … OVERLAPPING_LEAVE` | Your dates overlap a recorded request | Change the dates, or delete `requests.json` |
| `blocked … INSUFFICIENT_BALANCE` after earlier creates | Your earlier requests used the balance | Delete `outputs\requests.json` to reset |
| `PAST_DATE` | The festival has passed (demo dates age) | Use a later festival / offset |
| `audit_error: AUDIT_WRITE_FAILED` | The run was saved but the log could not be written | Check folder permissions; it is reported on purpose |
| `Invalid state transition` | You changed the state machine | Restore the `ALLOWED` table |
| `status: failed`, `code: STORE_READ_FAILED` | `outputs
equests.json` is corrupt or unreadable | Fix or delete it (the run fails *closed* — it refuses to guess) |

**The ALREADY_CREATED gotcha.** After one successful `--create`, running the same
`--create` again returns the original request **without asking you to confirm
and without checking the balance** — even if you would answer "no". The
idempotency check comes first. (A test run with an approval handler that always
*declines* still returned `created / ALREADY_CREATED`.) To see the approval prompt
again, change the request or **delete `outputs\requests.json`**.

## 7. Learn more

- **State machines** — finite-state machines as a design tool; the `ALLOWED`
  transition table is a tiny one.
- **Idempotency keys** — read how payment APIs (e.g. Stripe's documentation) use
  them to make retries safe.
- **Workflow engines:** Temporal, AWS Step Functions, Airflow, LangGraph — what
  they add (durability, retries, timers).
- **The saga pattern** and compensation for multi-step operations.
- **Audit logging** — append-only, tamper-evident, with retention.
- **Fail-closed vs fail-open** design.
- **Atomic file replacement** (`os.replace`) and why it protects a crash.
- **Concurrency control:** locks, optimistic concurrency, database transactions —
  the thing this local store does *not* have.

## 8. What you might be missing

- **This is deliberately boring, and that is the lesson.** Every status above is
  predictable. The cost: it handles *exactly* what it was built for. A request it
  does not understand is blocked, not improvised. Choose boring whenever you can.
- **Where is the model?** In this folder there is none. In a real system a model
  would still turn "can I take the day after Diwali off?" into the structured
  call (`user`, `festival`, `offset`, `days`) — then **hand it to code**. The
  README says: *"the model may interpret a user's request, but eligibility and
  creation are decided by `workflow.py`."* Try building that front end yourself;
  it is a good extension.
- **The ID can be guessed.** `LR-<hash>` is derived from public inputs. Fine for a
  demo; a real system needs an unguessable server-side ID and an authorisation
  check before returning one.
- **It is single-process teaching code.** The check "does this key exist?" and the
  write "append this record" are not atomic *together*. Two simultaneous requests
  could both pass the check. A customer system needs a database transaction or a
  lock. The README says so; do not skip over it.
- **There is no identity.** `--user E104` is just a flag. Anyone can claim to be
  anyone.
- **Approval is a typed word, not a manager.** "Approval" here is the *requester*
  confirming their own request. Real leave needs an approver who is a *different
  person* — the biggest gap between this demo and an HR process.
- **Balance logic is simplistic.** It subtracts the days of every recorded request
  regardless of leave type or date; there is no accrual, carry-over or public
  holiday calendar.
- **Leave type exists in the code (`annual` / `sick`) but the command line does not
  expose it** — everything you create is `annual`.
- **A failed audit write is reported but does not undo the record.** That is a
  conscious choice (`audit_error`), and a debatable one — discuss which way you
  would go and why.
- **Dates:** `today` is the machine's date. The demo festivals age out, so tests use
  a fixed date. Time-dependent logic needs an injectable clock — notice that
  `LeaveWorkflow` accepts `today=` for exactly this reason.
- **`runs.jsonl` grows forever.** Nothing rotates or prunes it.
- **Compare honestly with Day 11.** A fixed workflow is better here; that does not
  mean agents are never right. Day 13 asks you to decide *when* each is.

## 9. Where this leads

Day 13 designs a pilot using these controls (approval, idempotency, audit) as
requirements. Day 15 turns "ten identical decisions" into regression gates. Day
16 adds traces so you can *see* a run's states.
