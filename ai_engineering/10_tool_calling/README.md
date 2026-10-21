# Day 10 — Tool Calling and Controlled Actions

This local Enterprise Knowledge & Action Assistant demonstrates native model tool requests without giving the model execution authority. Exactly two tools are registered:

1. `lookup_internal_knowledge` — read-only retrieval through the existing Day 07 adapter.
2. `create_service_request` — a simulated local write that requires application permission and explicit human confirmation.

No shell, unrestricted filesystem, browser, email, database, or live ticketing tool is exposed.

## Architecture

```text
User message
    ↓
Local Ollama model receives exactly two JSON tool schemas
    ↓ proposes a structured call; it does not execute it
Application ToolRegistry
    ├─ parse JSON and reject unknown tools/fields
    ├─ validate types, enums, lengths, and ranges
    ├─ use application-owned actor permission
    ├─ read: execute retrieval
    └─ write: display proposal → require typed CONFIRM → persist atomically
    ↓
Validate structured tool result
    ↓
Append bounded/redacted JSONL audit event
    ↓
Return tool result to model for a truthful final response
```

The application interface is `ControlledAssistant.handle(message, actor=..., confirmation_handler=...)`. It returns:

```json
{
  "ok": true,
  "correlation_id": "application-generated-id",
  "final_response": "Model response after seeing validated tool results.",
  "tool_activity": []
}
```

This interface is independent of a terminal or future UI.

## Tool schemas

### `lookup_internal_knowledge`

```json
{
  "query": "What is the expense claim deadline?",
  "category": "expense_policy",
  "top_k": 3
}
```

- `query`: required non-empty string, maximum 500 characters.
- `category`: optional; `expense_policy` or `travel_policy`.
- `top_k`: optional integer from 1 through 5; default 3.
- Additional properties are rejected.

The normal backend calls Day 07's retrieval-only `rag.day06_adapter.search`, preserving chunk ID, source, original text, heading, page, similarity score, and rank. Day 06 vectors are never modified or regenerated.

Because Day 06 and Day 10 both use a package named `src`, the adapter opens a short isolated import window and still delegates search to the existing Day 07 interface.

`KNOWLEDGE_BACKEND=mock` is an explicit offline fallback. It searches [mock_knowledge.json](data/mock_knowledge.json), uses `mock_` IDs, and labels the response backend as `mock`. It is never represented as live Day 07 retrieval.

### `create_service_request`

```json
{
  "title": "Request database access",
  "description": "Access is needed for the analytics project.",
  "priority": "normal"
}
```

- `title`: required non-empty string, maximum 120 characters.
- `description`: required non-empty string, maximum 2,000 characters.
- `priority`: required enum: `low`, `normal`, or `high`.
- Additional properties—including actor or permission fields—are rejected.

The model call is only a proposal. The application first checks `ActorContext.can_create_service_request`, displays a human-readable summary, and requires the confirmation handler to return true. The CLI handler returns true only when the human types exactly `CONFIRM`.

Confirmed records are written to `outputs/actions/SR-<id>.json` using a temporary file, flush, `fsync`, and atomic replacement. The tool never calls an external service. Rejection returns `cancelled`; denied permission returns `permission_denied`; failed persistence returns `execution_error` and never claims creation.

## Responsibility boundary

| Model may | Application must |
|---|---|
| Suggest one of the registered tool calls | Parse and validate arguments |
| Ask a clarifying question | Supply actor identity and permissions |
| Read validated tool results | Ask the human to confirm writes |
| Summarize the real outcome | Execute tools and validate outputs |
| | Enforce duplicate and round limits |
| | Persist records and write audit logs |

Confirmation text cannot come from the model. Confirmation also cannot override denied permission.

Retrieved documents are untrusted data. The system prompt and application boundary instruct the model not to obey embedded instructions, while the registry prevents retrieved text from invoking any tool directly.

## Model integration

`OllamaModelClient` sends native Ollama tool definitions and accepts native structured tool calls. The URL, model, timeout, and maximum tool rounds are configurable. No model is downloaded automatically.

`ScriptedModelClient` supplies deterministic replies for unit tests and offline demonstrations. Mock execution is clearly separate from optional live Ollama integration.

An explicitly labelled offline demonstration can be run without Ollama:

```powershell
python -m src.assistant --demo lookup --message "Run the scripted lookup demonstration."
python -m src.assistant --demo ambiguous --message "Can you take care of this?"
python -m src.assistant --demo write --allow-write --message "Run the scripted write demonstration."
```

Demo output says `SCRIPTED MOCK MODEL`, lookup activity reports backend `mock`, and the write still requires real terminal confirmation.

Malformed JSON, unknown tools, duplicate IDs, invalid arguments, missing model responses, unavailable Ollama, timeouts, and tool-call loops produce controlled error codes.

## Logging

Every tool attempt appends one JSON object to `outputs/logs/tool_execution.jsonl` with timestamp, correlation/call IDs, validation status, permission decision, confirmation result, execution/result-validation status, duration, error code, and simulation flag.

Logs store query/title/description lengths, categories, priority, and key names—not free-text descriptions or retrieved document content. Known credential fields are redacted. Production systems would require centralized immutable audit storage, retention controls, monitoring, and broader secret detection.

## Normal and failure examples

Read-only request:

```powershell
python -m src.assistant --message "Use the knowledge tool to find the expense claim deadline."
```

Simulated write with application permission:

```powershell
python -m src.assistant --allow-write --message "Create a normal-priority database access request for the analytics project."
```

The action is created only after the terminal displays the proposal and the user types `CONFIRM`. Any other input cancels it.

Security boundary examples covered by tests:

- An unauthorized actor is denied before confirmation is requested.
- A rejected confirmation creates no file.
- A model-supplied `actor` property is rejected.
- An unregistered `run_shell` call is rejected.
- Malicious instructions in retrieved text remain inert evidence.
- A duplicate tool-call ID cannot execute twice.

## Tests and evidence

The default suite uses deterministic mocks and temporary directories. It covers the six requested scenarios plus schemas, outputs, read-only behavior, atomic persistence, permission/confirmation, failures, ambiguity, injection, unknown/duplicate tools, round limits, timeout, logs, and redaction.

The optional `integration` test requires the real Day 07 index, Ollama, and a model that actually supports tools. It is disabled unless `RUN_DAY10_INTEGRATION=1`. A skipped or blocked integration run is not evidence that live tool calling passed.

See `outputs/test_results/implementation_status.md` for the latest locally observed execution status.

## Trade-offs and limitations

- Local Ollama support varies by model; a configured model may ignore or mishandle native tools.
- Day 07 retrieval loads a local embedding model and can have higher first-query latency.
- Category filtering is based on trusted heading metadata after retrieval, not a dedicated filtered vector index.
- JSONL append logging is appropriate for a local exercise, not a multi-host production audit system.
- Local permission configuration is demonstrative, not authentication. Production identity, RBAC/ABAC, tenant isolation, approval workflows, idempotency, rate limits, monitoring, and incident response must be integrated outside the model.
- Tool schema changes are an API change: update schema, validators, model descriptions, tests, logs, and downstream UI together.

## FDE/customer implication

For a customer deployment, the important work is rarely just connecting a model to an API. An FDE must map real identity and authorization, define confirmation UX, establish idempotency and audit requirements, test failure and rollback behavior, measure model/tool reliability, and agree on who maintains schemas when business systems change. Start with read-only access, earn trust through traceability, and add narrow writes only after controls are proven.

See [SETUP.md](SETUP.md) for exact Windows commands.

