# Learnings — notes for the presentation

Keep adding to this while you work. Sections follow the presentation brief:
architecture decisions, coding-agent use, tool selection, testing and deployment, challenges.
Entries marked TODO need your own experience.

## Architecture decisions

- Clean Architecture with the dependency rule checked in practice: the domain and application unit tests run
  with no FastAPI, Pydantic or SQLAlchemy installed (ADR-001).
- Ports for persistence, LLM and ERP, adapters chosen in one file (ADR-003, ADR-004, ADR-006).
- Price ties raise an error instead of `min()` picking silently (ADR-002) — a good example of a decision
  where the whiteboard idea was changed on purpose and recorded with its alternatives.
- Use cases kept single-purpose: validation (budget) is separate from order creation (approval routing).
- All ADRs are Proposed. TODO: accept, change or reject each as a team and record who and when.

## Coding agent use

- Autonomy: semi-autonomous. The agent proposed structure and code; the team reviewed and corrected
  (Lecture 1, levels of autonomy). TODO: state which tool you used for which phase.
- Reflection in practice, concrete cases from this project:
  - The first plan ignored `SKILL.md` and progressive disclosure; a review against Lecture 2 caught it.
  - The first implementation did not match the agreed JSON contract (`stockCheck`, `nextState`, camelCase)
    or the whiteboard's last workflow states; a comparison against the sketch caught it.
  - Reading the professors' current template showed the ADR format needed an Alternatives section and that
    ADRs must stay Proposed until a human accepts them; the agent had marked them Accepted itself.
  - A static code review (no runtime available) found a foreign-key violation waiting in the approval
    integration tests and a missing status check in `RecordApprovalDecisionUseCase`.
- Honest limit: the scaffold's tests and code were generated together, so its history has no red step.
  Later work should commit the failing test first. TODO: add one real red → green example from your own work.
- TODO: one agent suggestion you kept and one you rejected, with the tool that produced each.

## Tool selection

Stack and reasons: `docs/PROJECT.md` (Dependencies) and the ADRs. The comma-separated columns for approval levels
and history are a prototype shortcut; a real system would use an audit table.
TODO: any tool you evaluated and dropped.

## Testing and deployment

- Pyramid: unit (no DB) → integration (Postgres, SAVEPOINT rollback) → e2e (`TestClient`, dependency overrides).
- Verified so far: 64 unit tests and `demo.py`. Not verified: SQLAlchemy layer, integration and e2e tests, Docker,
  CI, deployment. TODO: after the first CI run, note what failed and what you changed.
- TODO: after deployment, record the smoke test on the live URL — a green CI run is not evidence of a deployment.

## Challenges and lessons learned

- Three sources had to be reconciled (course template, teammate prompt, whiteboard) before writing code.
- The development environment had no network access, so the most infrastructure-heavy code could only be reviewed,
  not run — the top item in `docs/TASKS.md`.
- TODO: what took longer than expected, what was wrong at first, what you would change with five more weeks.
