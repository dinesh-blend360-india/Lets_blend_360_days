"""Deliberate faults from the Day 16 scenario document, switched on by flag.

Every fault is OFF unless the FAULT environment variable names it, so normal
runs are unaffected. One fault at a time, as the scenarios instruct:

    FAULT=slow_tool      F16-01  latency      3 s delay inside the lookup tool
    FAULT=flaky_tool     F16-02  error+latency first 2 tool calls time out, then succeed
    FAULT=mcp_error      F16-03  error        the tool layer returns an MCP transport error
    FAULT=bad_retrieval  F16-04  quality      lookup results are dropped
    FAULT=prompt_bloat   F16-05  cost+latency every chunk is sent instead of the top few

F16-06 is a data case, not a flag: it is a message containing personal data,
used to show the masking rules working.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


FAULTS = ("slow_tool", "flaky_tool", "mcp_error", "bad_retrieval", "prompt_bloat")

# Kept small and explicit so a trace can be matched back to the knob that caused it.
SLOW_TOOL_DELAY_SECONDS = 3.0
FLAKY_TOOL_FAILURES = 2


@dataclass(frozen=True)
class FaultConfig:
    name: str | None = None

    @classmethod
    def from_environment(cls) -> "FaultConfig":
        return cls(cls.parse(os.getenv("FAULT")))

    @staticmethod
    def parse(value: str | None) -> str | None:
        name = (value or "").strip().lower()
        if not name or name in {"none", "off", "0", "false"}:
            return None
        if name not in FAULTS:
            raise ValueError(f"Unknown FAULT {name!r}; expected one of {', '.join(FAULTS)} or no value")
        return name

    @property
    def active(self) -> bool:
        return self.name is not None

    def is_on(self, fault: str) -> bool:
        return self.name == fault

    def as_dict(self) -> dict[str, str | None]:
        return {"fault": self.name}
