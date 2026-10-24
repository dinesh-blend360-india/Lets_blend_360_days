# Pre-run corpus gap analysis

This is a source audit, not a generated evaluation run.

The configured Day 06 manifest indexes 11 chunks from the Day 05 employee expense and travel policy. Inspection of the source and `metadata.json` found no annual leave, vacation leave, leave approval threshold, international-trip business-unit approval, parental leave, or sick leave policy. These seven cases have primary stage `CORPUS_COVERAGE` and status `BLOCKED_MISSING_SOURCE`.

The receipt threshold is present in `chunk_5762afc8dde2640e56dd`, under `Employee Expense and Travel Policy > 2. Expense Reimbursement Rules > 2.1 Submission deadline and required context`. It states that a readable receipt is required for each expense of 500 currency units or more. Runtime retrieval rank, context inclusion, generation, and citation mapping remain untested because Python and Ollama are unavailable in the current shell.

