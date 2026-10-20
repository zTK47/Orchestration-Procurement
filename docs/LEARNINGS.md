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
- Verified: 141 unit, 12 integration (PostgreSQL 16) and 13 e2e tests, `ruff`, `demo.py`; the Docker build and all
  CI jobs are green on the migration pull request (2026-10-20). Not verified: deployment.
- The first CI run in this repository passed without changes, because the suite had already been run against a
  local Postgres before the migration.
- TODO: after deployment, record the smoke test on the live URL — a green CI run is not evidence of a deployment.

## Challenges and lessons learned

- Three sources had to be reconciled (course template, teammate prompt, whiteboard) before writing code.
- The development environment had no network access, so the most infrastructure-heavy code could only be reviewed,
  not run. Resolved on 2026-10-01: the full suite passed against a local Postgres.
- The first repository had edited the template's own files (`AGENTS.md`, skills, scripts, workflows). The project was
  moved into a fresh copy of the template, keeping its structure and adding only project files.
- Work an agent produces in a cloud session exists only in that session until it is committed and pushed: one README
  draft was lost this way. Commit and push early.
- The agent's permission system blocked it from wiring an automatic production deployment on its own. Deployment
  stays a human decision (AI-SDLC phase 5: "defined together with the user").
- TODO: what took longer than expected, what was wrong at first, what you would change with five more weeks.
