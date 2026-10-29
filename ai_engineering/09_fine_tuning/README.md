# Day 09 — Architecture Decisions and Fine-Tuning Foundations

Day 09 teaches how to choose the simplest defensible architecture for a business requirement. It does not train a model. The project runs locally with deterministic validation and scoring—no API key, GPU, cloud service, model, RAG system, or vector database is required.

## Decision workflow

```text
Business outcome and constraints
              ↓
Classify the primary problem
knowledge | behavior | action | deterministic | unknown
              ↓
Complete an Architecture Decision Card
              ↓
Choose the smallest suitable architecture
PROMPT_CONTEXT | RAG | FINE_TUNING | COMBINATION | NO_LLM
              ↓
If essential facts are unknown: DECISION_DEFERRED
              ↓
Validate against a baseline and measurable acceptance criteria
```

An **action** problem means the system must cause a controlled external change. Day 09 does not implement actions, but the decision must identify permissions, confirmation, idempotency, and audit requirements before adding tools or automation.

## Choosing an approach

| Primary need | Usually start with | Why |
|---|---|---|
| Bounded transformation or tiny supplied source | `PROMPT_CONTEXT` | Least infrastructure; pair with schema validation and abstention rules. |
| Current, private, or frequently changing knowledge with citations | `RAG` | Keeps knowledge outside model weights and provides source evidence. |
| Persistent specialized behavior after a measured prompt baseline fails | `FINE_TUNING` | Can improve stable task patterns when reviewed representative examples exist. |
| Changing knowledge plus unresolved persistent behavior | `COMBINATION` | RAG owns knowledge; tuning may improve behavior if evaluation justifies it. |
| Exact reproducible business rules | `NO_LLM` | Deterministic code is safer, testable, versioned, and auditable. |
| Essential outcome or constraints are unknown | `DECISION_DEFERRED` | Discovery is required before an architecture can be defended. |

Fine-tuning is not the default. It does not guarantee factual accuracy, current knowledge, or citations. It is mainly useful for durable behavior, formatting, and task-specific patterns supported by good data and evaluations.

## Reference scenarios

| ID | Scenario | Reference decision |
|---|---|---|
| S01 | Small meeting-note transformation | `PROMPT_CONTEXT` |
| S02 | Frequently changing internal policies | `RAG` |
| S03 | Inconsistent specialized behavior with reviewed examples | `FINE_TUNING` |
| S04 | Current manuals and release notes | `RAG` |
| S05 | Reproducible eligibility rules | `NO_LLM` |
| S06 | Current private knowledge plus specialized behavior | `COMBINATION` |
| S07 | One short, rarely changing policy | `PROMPT_CONTEXT` |
| S08 | “Fine-tune company data” without requirements | `DECISION_DEFERRED` |

The initial recommendation is not unconditional. Each record in [architecture_scenarios.json](data/architecture_scenarios.json) contains assumptions that could change the decision. Completed reference cards are in [reference_decision_cards.json](data/reference_decision_cards.json).

Scenario 6 is deliberately staged:

1. Establish and freeze a RAG baseline.
2. Measure remaining behavior failures.
3. Review and split representative examples.
4. Fine-tune only the behavioral component.
5. Compare the combined system with the baseline before release.

Scenario 8 deliberately does not choose RAG or fine-tuning. It awards credit for identifying unknowns about outcomes, knowledge versus behavior, freshness, citations, training data, privacy, deterministic requirements, targets, and prior baselines.

## Architecture Decision Card

The reusable schema is [decision_card_schema.json](data/decision_card_schema.json). Required fields cover outcome, problem type, knowledge and freshness, citations, data, privacy, cost, chosen approach, rationale, rejected alternative, risk, discovery, and validation. `staged_approach` is the only optional decision-card field and is required by validation for S06.

Example:

```json
{
  "scenario_id": "S05",
  "business_outcome": "Make reproducible eligibility decisions.",
  "problem_type": "deterministic",
  "knowledge_source": "Versioned explicit rules",
  "knowledge_freshness": "Controlled rule releases",
  "citation_requirement": "Rule version and audit trace",
  "data_availability": "Rules and inputs are explicit",
  "privacy_security": "Protect inputs and audit logs",
  "latency_cost_constraints": "Predictable low latency",
  "chosen_approach": "NO_LLM",
  "why_this_approach": "Code is reproducible and auditable.",
  "rejected_alternative": "PROMPT_CONTEXT",
  "rejected_alternative_reason": "Generation cannot guarantee identical decisions.",
  "key_risk": "Incorrect rule implementation.",
  "discovery_question": "Can every criterion be represented explicitly?",
  "validation_plan": "Run decision tables, boundary tests, and rule regressions."
}
```

## CLI workflow

From `09_fine_tuning`:

```powershell
python -m src.scenario_loader --list
python -m src.scenario_loader --show S06
python -m src.scenario_loader --export-template S01
```

Edit `submissions\S01_submission.json`, then evaluate it:

```powershell
python -m src.decision_evaluator --submission submissions\S01_submission.json
```

The evaluator uses a visible 100-point rubric:

- architecture alignment: 25
- problem identification: 15
- requirements alignment: 15
- rejected alternative: 10
- key risk: 10
- decision-changing discovery question: 10
- practical validation plan: 10
- staged approach: 5, required for S06 and treated as not applicable/full credit elsewhere

Keyword matches and every dimension score are included in the JSON result. This makes scoring reproducible and inspectable, but lexical matching cannot fully judge reasoning quality; review the explanation manually as well.

Reports are written to `outputs\run_history\<UTC-run-id>\` without overwriting prior runs. `outputs\reports\latest_report.md` contains the latest readable report.

## Fine-tuning readiness

Create a readiness checklist:

```powershell
python -m src.fine_tuning_readiness --export-template submissions\fine_tuning_readiness.json
```

Edit each item to `READY`, `NOT_READY`, or `NEEDS_REVIEW` with an evidence-based reason, then assess it:

```powershell
python -m src.fine_tuning_readiness --assess submissions\fine_tuning_readiness.json
```

The checklist covers the behavioral problem, prompt baseline, reviewed dataset, train/validation/test split, data quality, sensitive data, evaluations, base model, cost/latency, and deployment/maintenance. It never fabricates examples or starts training.

## Limitations and future improvements

- Deterministic keyword scoring is transparent but cannot fully evaluate semantic reasoning.
- Reference decisions depend on stated assumptions; real discovery can change them.
- The readiness assessment verifies documented status, not the underlying dataset or model.
- Actual dataset preparation, tuning, deployment, and model comparison are future work.
- A future version could add human review notes and calibrated rubric versions while preserving historical results.

See [SETUP.md](SETUP.md) for exact Windows commands.

