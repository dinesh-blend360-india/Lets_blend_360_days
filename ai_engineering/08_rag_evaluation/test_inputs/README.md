# Evaluation dataset

`day08_common_cases.json` contains the eight stable Day 08 cases. Expected evidence is based on the configured Day 06 structure-aware index, not on assumptions in the assignment.

Corpus audit: the index has 11 chunks from `Day5_document_Chunking_Samples\employee_policy_markdown_sample.md`. It covers expenses and business travel. Annual leave, vacation leave, leave approval thresholds, international-trip business-unit approval, parental leave, and sick leave are absent. The receipt threshold is present in `chunk_5762afc8dde2640e56dd` and is **500 currency units or more**.

`MISSING_FROM_CORPUS` cases deliberately have no expected chunk IDs. They are reported as `BLOCKED_MISSING_SOURCE`; a model abstention is useful behavior, but not proof of retrieval quality.

