# Day 14 MCP

This local stdio MCP server exposes one existing safe capability: Day 10's `lookup_internal_knowledge`. The tool keeps Day 10's argument and result validation. It is read-only and makes no service request. The client discovers the tool and calls it for a normal lookup and an empty-query failure.

MCP supplies capability discovery and a request/result protocol. It does not decide what the assistant should do next. The application still owns user identity, authorization, approval for actions, and interpretation of untrusted retrieved text. This local exercise has no enterprise authentication; do not expose its transport to untrusted clients.

Run from this directory with Python 3.11+:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r ../requirements.txt
python client.py
python -m pytest tests -q
```

The client explicitly selects Day 10's `mock` backend, so returned chunks are demo data. For a real Day 07 lookup, configure `KNOWLEDGE_BACKEND=day07` and the Day 06 index before connecting. The client prints discovered schema, successful result, and handled validation failure; save that JSON as evidence if submitting the exercise.

The implementation uses the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) and its [stdio client transport](https://py.sdk.modelcontextprotocol.io/client/transports/). The server's only tool comes from Day 10; a future write tool would need the same trusted permission and confirmation boundary as Day 10's application.
