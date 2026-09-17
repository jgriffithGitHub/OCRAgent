# CLAUDE.md — OCRAgent Project Instructions

This file is the stable, repeatable process contract for this repo. It exists
so that guidance doesn't have to be re-derived (and doesn't drift) every time
a coding agent — or a person — starts a new session here. If something in
this file turns out to be wrong or incomplete, fix the file; don't just fix
the one conversation.

## Source of Truth — Don't Duplicate, Point

The project is also attached to a claude.ai Project ("ORCAgent") whose
description covers the same process framing at a high level, for chats that
aren't working directly in this repo. That description isn't a substitute
for this file — it isn't visible to anyone outside that Project (a GitHub
reviewer never sees it), and it isn't guaranteed to be read the same way
`CLAUDE.md` is by every tool. Treat this file as the authoritative copy.

## Process Note

The development process is defined in `PROCESS.md`. It is currently a "work-in-progress"
so it is expected there are many problems to be discovered and resolved. When you
see a problem, please escalate the problem and ask Jeff to resolve it. Suggestions
are welcome, but do not assume a particular solution will be implemented (while
the solution to a specific problem may be obvious within the stated process, 
Jeff may rewrite the process instead).

## Roles

This project is deliberately run with three distinct roles, not one blurred
agent doing everything. These roles are defined in `ROLES.md`.


## Standing Rules (apply regardless of who — or what — is working)

1. **Never guess when you lack signal. Say so instead.** This is not a
   style preference; it is the product's core differentiator (see
   `docs/Requirements.md` FR-6) and it applies recursively to how this repo
   itself gets built: if a requirement, a test result, or a design choice is
   genuinely unclear, flag it as a gap rather than filling it in with a
   plausible-sounding assumption. Silently guessing here undermines the
   exact thing this tool exists to avoid doing. Suggestions are always welcome.

2. **Data Transport:** all data exposures must be known and stated. There is
    significant concern that data processed by LLMs is being used to train
    the next generation of models and businesses do not want their intellectual property
    in that training data.
    
3. **Default coding mode: explain and scaffold, don't solve.** Unless
   explicitly asked to implement something directly, prefer explaining the
   data structures/types and approach involved and let the core logic be
   written by the human author. Boilerplate, scaffolding, config, and tests
   are fine to generate outright. This default can be overridden per-task —
   if Jeff asks for a direct implementation, do that — but don't assume
   "just write it" is the default mode in this repo.

4. **Don't extend `history/testAgent/`.** It's a retired prototype kept for
   reference (it's what proved the OCR+LLM approach worked at all, and its
   bugs/fixes are documented in `history/session-summary.md`). New
   implementation work belongs in `product/src/`, informed by but not built on top
   of the prototype's code.

## Repository Map

- `docs/` — intent statement, requirements, and the live gap list. Start
  here to understand *what* is being built.
- `docs/ADRs` — The home for Architectural Decision Records
- `docs/architecture_reviews` — A place for raw notes that identify review findings to be addressed. The findings are addressed by ADRs
- `docs/intent_reviews` — Point-in-time reviews of `docs/Intent.md`, produced by running `prompts/IntentReviewPrompt.txt`. One file per review pass; the review itself doesn't change `Intent.md`, it just informs the next edit to it.
- `history/` — An unstructured collection of artifacts that support an
  understanding of `how` and `why` this project has reached its current state.
  The retired `testAgent` prototype (OCR+LLM proof of concept)
  and `session-summary.md`, its origin story. Reference only — see Rule 4.
- `tasks/` — discrete units of work. Acceptance tests and validation tasks called out
  in `docs/Requirements.md` (e.g., the cold-start network isolation test
  required by NFR-10 — see that section for what the task needs to prove) 
  are defined in `tests\`.
- `tests/` — automated process tests that define if a task is complete.
- `changelog/` — process change history.
- `product/` — everything for the product, to keep it separate from the process.
- `product/src/` — the actual implementation. Currently empty; this is where the
  real system gets built once enough of the requirements/design gaps are
  closed to start.
- `product/agent/` — any agentic resources required by the product  
- `product/build/` — anything needed to create the deliverable from the src  
- `product/tests/` — product level test documentation  
- `product/ops/` — anything needed to implement and/or maintain the CI/CD pipeline
- `product/review/` — code reviews live here
- `product/changelog/` — product change history.
- `templates/` —  this is a collection of files to be used as templates to create process documents 
- `prompts/` — the home for process-level prompts (e.g. `IntentReviewPrompt.txt`). Now part of
  the process, not just Jeff's reference material — see `docs/intent_reviews/` for where its output lands.
- `code_review/` —  a place for process-related specs for code reviews, specifically the `pyproject.toml` file
- `private/` — Jeff's personal scratchpad. Not part of the process; nothing here should be assumed to
  reflect a process decision, and this repo's process docs should never be written to expect this folder to exist.

Every project needs at least the following artifacts, stored in the following locations:

- This file (`CLAUDE.md`) — *how* to work in this repo, not *what* the
  product does. If you find yourself restating product requirements here,
  that content belongs in `docs/Requirements.md` instead. An `AGENT.md` file is
  not added here since Anthropic's Claude platform is the agent for the process.
  However, an `AGENT.md` file might be part of the product which would cause
  that file to be included in the "src" folder tree.
- `docs/Intent.md` — the original business intent (what problem
  this solves and why).
- `docs/Requirements.md` — functional requirements, non-functional
  requirements, business rules, permissions, constraints, and acceptance
  criteria, derived from the intent statement. **Includes a live gap list**
  of things the intent/requirements don't yet resolve — check it before
  assuming something is decided.
- `docs/Requirement_Traceability_Matrix.csv` — a map showing how requirements are fulfilled
- `docs/ADRs/ADR-xxxx.md` — individual architectural decision records
- `docs/features/FEA-xxxx.md` — individual feature definitions
- `tasks/Task-Index.md` — A summary of all the tasks and their status
- `tasks/Task-xxxx.md` — individual tasks for Cowork and Claude Code
- `tests/Acceptance-Tests-0000.md` — At least one of these for each task 
  that defines when the task is done.
- `product/src/README.md` — A guide to the source and the build process, along
  with other useful developer notes. Detailed information may be provided elsewhere
  but a pointer to it needs to be in here.
- `product/tests/Test-Plan.md` — The product feature test plan
- `product/tests/Unit-Test-0000.md` — product feature level test descriptions 
- `product/tests/Integration-Tests.md` — the functional test plan for the external interfaces
- `product/tests/Failure-Test-0000.md` — if needed, describe how to test against known
  or stated product limits (e.g. what should happen if an API is flooded with requests). 
- `product/review/Review-Log.md` — a list of code review files
- `product/agent/Context-Pack-0000.md` — These files provide supplementary details that Cowork
   and Claude Code need to complete a task. 
- `product/agent/Prompt-Library-0000.txt` — the prompts used by the product to guide agents 
- `product/ops/Deployment-Checklist.md` — the full set of installation instructions in checklist format
- `product/ops/Maintenance-Notes.md` — notes and lessons learned about the CI/CD and delivery processes

## Environment (known-good, not yet re-validated for `src/`)

These versions are what the retired `history/testAgent` prototype ran on
successfully (Windows). They are **not** confirmed as the environment for
the actual `product/src/` implementation yet — re-verify before relying on them:

- Python venv; `paddleocr==3.7.0`, `paddlex==3.7.2`, `paddlepaddle==3.2.2`
  (3.3.1 has a confirmed oneDNN/PIR regression — see `history/
  session-summary.md`), `opencv-contrib-python==4.10.0.84`, `numpy==2.3.5`,
  `pillow==12.3.0`.
- Ollama running locally, model `qwen3:4b` (send `"think": false` in the
  chat request — Qwen3 defaults to emitting a visible reasoning trace
  otherwise).
- NFR-10 in `docs/Requirements.md` documents an open question about
  whether this stack makes any outbound network calls on a cold start
  (cache cleared / offline). That has not been tested yet — don't assume
  "runs fully local" is proven until that task exists and passes.

## Before Starting Any Work

Check `docs/Requirements.md`'s Consolidated Gap List. As of this file's
creation there are 14 open gaps (G-1 through G-14), including the interface
contract for how other agents call this tool (G-1), the confidence
scale/threshold (G-5 — the single most consequential one, since it
underlies the tool's core differentiator), and permissions/auth (G-11,
currently unaddressed). Building against an unresolved gap without flagging
it repeats the exact mistake Rule 1 exists to prevent.

## Git / Repo Hygiene

`.gitignore` intentionally excludes `history/testAgent/pdf_inputs/`,
`history/testAgent/outputs/`, and `history/testAgent/logs/`. That's a
deliberate content-licensing decision, not an oversight: samples are mostly
synthetic, but include one real document (Jeff's own toll receipt) and
several third-party logos Jeff doesn't have redistribution rights to. Don't
re-add them or replace them with new "real-looking" samples without
checking that decision first.

## Python Coding Standards

**Formatting & imports — enforced, not described.**
Run `ruff format .` and `ruff check --fix .` before any task is done. Non-negotiable, not a suggestion. Config lives in `code_review/pyproject.toml` — don't restate indentation, quotes, or import order here.

**Naming**
- snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for module-level constants.
- Booleans read as a question: `is_`, `has_`, `should_`.
- No invented abbreviations; spell it out unless it's already standard in this codebase (`ocr`, `pdf`, `llm`, `cfg`).

**Paths**
Always `pathlib.Path`. Never string concatenation, never hardcoded `\\` or `/` separators.

**Error handling**
- Catch specific exceptions, not bare `Exception`, unless the boundary is genuinely "any failure here should degrade gracefully" — and say so in a comment when you do.
- Never collapse a caught error into a same-shaped success value silently. Log it (`logging`, not `print`) and either re-raise or return a distinguishable failure.
- No bare `print()` for status/progress — use `logging` so output stays filterable and consistent across every script.

**Type hints**
Every new function signature gets parameter and return type hints. (Not retrofitted onto existing code unless you're already touching that function.)

**Comments & docstrings**
- One-line docstring per function: what it does, not how.
- "Why" comments (library quirks, workarounds, version-specific bugs) go directly above the line they explain — keep doing this, it's already a strength of this codebase.
