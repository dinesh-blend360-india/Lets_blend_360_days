# Completeness rubric

Use this criterion only for questions with a supported reference in the configured corpus. Judge the final answer against the question, retrieved tool results, and the case's expected behavior. This rubric cannot decide permissions, schema validity, or whether a write was confirmed; code checks those.

| Verdict | Observable rule |
|---|---|
| PASS | Every requested part is answered and each factual policy claim is supported by the supplied retrieved result. |
| FAIL | A requested part is missing, contradicted by the retrieved result, or asserted without supplied support. |
| UNSURE | The supplied result or question is too ambiguous to decide; identify the missing evidence. |

Example PASS: for a two-part expense and travel question, the answer gives both the 30-day mock claim deadline and the mock travel approval rule, each tied to its source ID.

Example FAIL: the answer gives only the claim deadline and omits travel approval.

The judge must return JSON with `verdict` and a short `reason`. It may not turn a failed hard gate into a pass. A reviewer should write blind labels before running the judge.
