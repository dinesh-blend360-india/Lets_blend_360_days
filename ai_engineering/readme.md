# simple Gen ai --> Day 1 - V1 of GEN AI applicatoin [7-oct]
#       - contains streamlit for GUI
#       - Simple text and response application

## Setup and run

**[RUN_GUIDE.md](RUN_GUIDE.md) — start here.** Prerequisites, one-time setup, and
the commands to run every day from 01 to 15, plus the dependency order between
days and a troubleshooting table.

## Learning path

Days 01–10 cover chat, context, structured output, developer tooling, document chunking, retrieval, RAG, evaluation, architecture choices, and controlled tool calling. The next sequence builds on those exercises:

| Day | Folder | Focus |
|---|---|---|
| 11 | [11_agents](11_agents/README.md) | Bounded agent loop over Day 10 tools; leave demo |
| 12 | [12_reliable_agentic_workflows](12_reliable_agentic_workflows/README.md) | Deterministic leave decisions, approval, idempotency, audit |
| 13 | [13_agentic_engineering](13_agentic_engineering/README.md) | Hypothetical pilot design and lifecycle evidence |
| 14 | [14_mcp](14_mcp/README.md) | Read-only Day 10 lookup through a local MCP server and client |
| 15 | [15_evaluations](15_evaluations/README.md) | Golden cases, hard gates, scripted baseline, judge calibration path |
| 16 | [16_observability](16_observability/README.md) | Nested tracing over Day 10, fault flags, masking, one diagnosed-and-fixed defect |

From this directory, launch the shared UI with `streamlit run hub/app.py`. Each day's README gives its standalone commands and evidence limits.
