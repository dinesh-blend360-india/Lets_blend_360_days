# Day 13 Agentic Engineering

The [design card](design_card.json) is a **hypothesis** for taking the existing Enterprise Knowledge & Action Assistant toward a controlled customer pilot. It does not claim a deployed system, measured production quality, a customer approval, or a completed security review. The current code evidence is in Days 10–12; proposed controls remain labelled `PROPOSED`.

The card covers the ten Agentic DevOps stages, owners and handoffs, three proposed golden cases, a pilot decision, recovery, unknowns, an alternative fixed workflow, and the top risks. Run `python validate_card.py` to check its structure.

## Engineering reflection

The biggest unvalidated assumption is access control: Day 10's local actor flag is a demo, while a customer deployment needs trusted identity and document-level authorization. The next experiment is a denied-access golden case using an explicit actor context and a source that would otherwise be retrievable.

The model should choose between answering, retrieving, and proposing a request. Code must own identity, permissions, schema checks, idempotency, and confirmation. A service timeout after a write is the most important failure to rehearse because a blind retry can duplicate the action. The release owner needs the approved tool result and idempotency status before reporting success.

A fixed workflow is the alternative. It offers lower variance and simpler review when tasks are known. An agent loop is justified only for requests where the next retrieval depends on what the preceding result contains. The first pilot should be read-only until the customer approves an action boundary and its recovery path.

The proposed pilot cannot start while authorization rules, data scope, or rollback ownership are unknown. Numeric targets for latency, quality, and cost must be agreed with the customer and measured, not invented here.
