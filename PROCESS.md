# Development Process

## Roles
Roles are defined in `ROLES.md`

## Workflow 
The workflow starts with the creation of the Intent description. This is the business vision for the project. It is not complete and 
there will be many gaps. However, it must be sufficiently detailed that a coherent scope can be derived from it. For example, the intent
statement of "I'm building a car." is not sufficient, but "I'm building a car that has three wheels to save fuel, travels 500 miles on a single
5 gallon tank of fuel, has supplemental solar power, holds one person and is typically used to commute less than 50 miles one way." is a better
start. In this example, the Intent statement will not cite all the related regulations; it can assume these will be added by the process.

Before -- and any time after -- Intent.md is edited, it can be reviewed against `prompts/IntentReviewPrompt.txt`,
which checks it for clarity, vision/implementation separation, identified users/goals/constraints, whether it
actually turns business needs into software direction, and ambiguity. This review does not change `Intent.md`
itself; it produces a dated report under `docs/intent_reviews/` that the Development Manager uses to decide the
next edit. It's optional but cheap, and worth running again after any substantive rewrite of `Intent.md`, not just
once at the start.

Commit `Intent.md` before running the review, not after. A review report only means something in relation to the
exact document it looked at; if `Intent.md` keeps changing in the working tree while reports pile up in
`docs/intent_reviews/`, the link between a given report and the version it reviewed exists only in whoever's memory
ran the review -- and that link is lost the moment someone forgets, or the next edit overwrites the reviewed version
before it's committed. (This happened during the process's first real test run: a second revision of `Intent.md` was
reviewed, then replaced by a third revision before either was committed, so the second revision itself is no longer
recoverable from git -- only the report describing its weaknesses survives.) Referencing the commit SHA in the
review report closes that gap cheaply.

Given the Intent document, several rounds of negotiation occur that refine it until a coherent set of requirements can be produced. 
The requirements are written using the `ProductRequirements_Template.md` as the format. It is expected that this document will evolve throughout
the development process as it is not possible to see all the requirements during initial review and requirements will change as people begin
to review the product. 

In the following discussions, all features are described using the `Features_Template.md`. The `TechnicalOverview_Template.md` provides a 
summary of all features (both architectural and product features).

Acceptance tests are defined in two passes. A test is written using the `Test_Template.md` file. In the first pass, all required tests can be 
identified, and a document started for each, by reviewing the requirements. The second pass occurs after features are defined. In this pass,
the test specification can be completed because the test verifies a requirement is fulfilled by exercising the features that implement it.

Requirements are reviewed to produce two sets of features: architectural features and product features. The feature sets are separated
because some requirements are global to the product or process. These global requirements (such as security or data storage requirements)
must be satisfied by a global service that is typically defined by the product or process architecture. The remaining requirements are
satisfied by product features that are built on and describe how the architectural features are used. 

To produce the set of architectural features, requirements (both functional and non-functional) are reviewed to produce an architecture which
identifies the foundational elements of the product or process and the interactions between the elements. The architecture is documented in
Architecture Decision Record documents created using the `ADR_Template.md`. Everything that can be built to implement this product or process
must work within this architecture. For example, the architectural statement for a service may state the service is cloud-based and can be
consumed by making an HTTP POST request to an endpoint. In this example, if there is a requirement for security, since it is common for 
security requirements to be implemented within the architecture, this example architecture definition could include ADRs that define a set of 
architectural features that state how the security requirements are addressed.

Product features define the means by which the capabilities of the architecture are deployed to solve one or more requirements. Requirements that are 
not fulfilled by the architecture must be fulfilled by product features. After the architecture is defined, each remaining requirement must be mapped
to one or more features and each feature must explicitly state how it addresses each mapped requirement. For example, a requirement may state that the
user will be able to provide a recipient's name and address. if the related architecture provides a client-server structure supporting React-based
single page web apps, a feature might address this requirements by describing a web app to accept this data.

After the features are defined (and when they change) the process must review how the architecture features and product features implement all requirements to
look for gaps, overlaps and conflicts. Architecture reviews are documented using the `Architecture_Review_Template.md` and written to the `docs/architecture_reviews/` directory.
The issues to be resolved are:
- gaps: has the architecture assumed data security would handled by the database but the database assumed that any user that had access was authorized or has one 
  feature implemented part of a requirement and a second feature has implemented part of requirement, but the two features together don't implement the full requirement
- overlaps: are users required to be authorized to use the product and to be authorized again to use a feature without a defined feature-based authorization requirement
- conflicts: are two features and/or the architecture implementing the same requirement in different ways .

Features (both architecture and product features) are the basis for all user documentation; it must be possible to describe the product or process to
a user solely from the feature set.

After the features are defined, the acceptance tests can be refined (this is the second pass mentioned previously). In this pass, since all requirements are
implemented by features and each test is mapped to a requirement, the test can be prepared that defines how the features associated with the tested requirement can
be applied to satisfy the requirement.

Features are implemented by tasks. Each task is defined by an instance of the `Task_Template.md`. A task must provide sufficient information that a coding agent
can implement it, test it and determine that it is acceptable given the information in the task. Every task must be traceable to at least one requirement and it must
reference at least one test.

Any APIs are documented using the `API_Specification_Template.md` template and databases are documented using the `Data_Database_Specification_Template.md` template.

The `Requirement_Traceability_Matrix.csv` needs to be updated as requirements and features are developed.

## Product Artifacts

The `docs/`, `tasks/`, and `tests/` chain above defines what is being built and why. The `product/` tree is everything
about how it actually gets built, run, and kept running -- and it needs the same kind of derivation, not just a list
of filenames.

`product/src/` is written by Developers (Claude Code) as tasks are implemented; nothing here is created ahead of a
task. `product/src/README.md` is started with the first task that produces real code (a guide to what's there and how
to build/run it cannot exist before there's something to guide) and is updated by every later task that changes how
the code is built, run, or organized -- treat "does this task change how someone else would build/run this?" as the
trigger for touching it, not a fixed schedule.

`product/agent/Prompt-Library-0000.txt` holds the prompts the *product itself* sends to its LLM at runtime (as
distinct from `prompts/` at the repo root, which is Jeff's own reference material for running this process, not part
of the product). It is written and updated the same way as any other part of `product/src/` -- by the task that
introduces or changes an LLM call -- and should be treated as source, not documentation: reviewed and versioned the
same way.

`product/agent/Context-Pack-0000.md` is optional, per task. When a task needs supporting material too bulky to put in
the task file itself (an API reference dump, a sample-document description, a design constraint that needs more than
a sentence), the Technical Supervisor (Cowork) creates a Context Pack alongside that task and the task references it
by ID. Most tasks won't need one.

`product/tests/Test-Plan.md` is the overall test strategy for the product (as opposed to
`tests/Acceptance-Tests-0000.md`, which is per-task and defines when *that task* is done). It's derived from the
feature set and the Non-Functional Requirements once both are stable enough to commit to a strategy -- created after
the first Architecture Review closes, and revisited on the same "after features are defined, and when they change"
trigger the Architecture Review itself uses.

`product/tests/Unit-Test-0000.md`, `Integration-Tests.md`, and `Failure-Test-0000.md` are all instances of
`Test_Template.md` -- currently the same template already used for acceptance tests -- scoped to a different test category
rather than a different format. `Task_Template.md` references these artifacts, the same way `## Acceptance Test:` 
in a task already points at `tests/Acceptance-Tests-0000.md` rather than restating it. 
`Integration-Tests.md` is singular (one plan, not one per task) and grows whenever an `API_Specification_Template.md` 
instance or an ADR introduces a new external interface. `Failure-Test-0000.md` is created only when a task or requirement 
states an explicit limit (a `LIM-xxxx` in `docs/Requirements.md`) that needs boundary testing -- "if needed," per 
its own description, not one per task.

`product/review/Review-Log.md` is the rollup (parallel to `tasks/Task-Index.md`) of individual code reviews. The
Technical Supervisor reviews a Developer's work -- including confirming `ruff format` / `ruff check --fix` were run
clean against `code_review/pyproject.toml` -- before signing off that a task's acceptance criteria are met (this is
already ROLES.md's description of Cowork's job; this just gives it a place to land). One entry per completed task,
referencing the Task ID.

`product/ops/Deployment-Checklist.md` is created once the first deployable increment of `product/src/` exists -- not
before, since there's nothing to install a checklist for until then -- and updated whenever a task changes a
dependency, an environment variable, or a setup step. `product/ops/Maintenance-Notes.md` is append-only: an entry
gets added whenever an ops or delivery lesson is actually learned (the way `history/session-summary.md`'s bug list
already reads, just for the product going forward instead of the retired prototype).

`changelog/` and `product/changelog/` are both append-only, and both get an entry for the same kind of event on their
own side of the process/product split: `changelog/` when this file, `PROCESS.md`, `ROLES.md`, or a template changes
(today's session -- the `product/` folder structure landing, the typo fixes, the `.gitignore` fix -- is exactly what
a first `changelog/` entry would describe); `product/changelog/` when `product/src/` changes in a way a future
maintainer would want to know about, independent of what any individual task's own record already says.

`tasks/Task-Index.md` is maintained by the Technical Supervisor, not generated once: it's updated whenever a task is
created or its status changes, so it stays a live summary rather than a snapshot.

## Known Process Gaps

Mirrors `docs/Requirements.md`'s own gap list, but for gaps in the *process* itself rather than the product. Each
entry gets a `PG-xxxx` ID. Logged here so an idea raised mid-session isn't lost before anyone decides whether to
act on it -- an entry sitting here is not a commitment to build it, just a flagged, findable open item.

### PG-0001 -- No elicitation step between Intent.md and Requirements.md

`docs/Intent.md` is meant to stay at "I have a good idea, not yet a spec" altitude. In practice, three rounds of
running it through `prompts/IntentReviewPrompt.txt` and revising pulled a lot of genuinely spec-level detail
straight into `Intent.md` itself -- confidence-score math with worked examples, PII handling, a performance number,
an input-format decision. None of that is wrong to have written down, but `Intent.md`'s fixed section structure has
no natural home for that level of detail, so it either gets awkwardly folded into a section that wasn't meant to
hold it, or it's lost until someone remembers to carry it into `Requirements.md` by hand.

The root cause: `IntentReviewPrompt.txt` is purely evaluative -- it finds weaknesses (unclear, ambiguous,
vision/implementation mixed) but doesn't elicit the missing specifics needed to actually support Requirements.md
generation. A concrete symptom Jeff raised: there's no good place in `Intent.md` for something like real user
interface capabilities, if a future project needs that. The process has no step that systematically walks an
intent statement forward into requirements-ready detail; right now that either happens by accident (as it did
here) or doesn't happen until someone drafts `Requirements.md` from scratch.

**Proposed direction (Jeff's, not yet decided or built):** expand `prompts/IntentReviewPrompt.txt` -- or add a
companion prompt alongside it -- into something closer to a "flesh out this intent" step: generative, not just
evaluative, built specifically to produce the detail `docs/Requirements.md`'s `ProductRequirements_Template.md`
actually needs. Open questions this would raise if picked up: does it replace `IntentReviewPrompt.txt` or run
after it; does its output still live in `docs/intent_reviews/` or does fleshed-out content move into `Intent.md`
directly; and does `Intent.md`'s section structure need to grow to hold what this step produces, or does the new
prompt's output become the actual first draft of `Requirements.md` instead.

**Decided approach (2026-09-18):** rather than design the missing intermediate document up front, discover it
empirically. Attempt to draft `Requirements.md` now from the current `Intent.md` and `ProductRequirements_Template.md`;
treat friction in that attempt as signal, not failure. Continue refining `Intent.md` as needed in the meantime, even
though holding this level of detail isn't really its intended role -- it's what exists. Once `Requirements.md`
reaches a genuinely good, clear state, diff `Intent.md` v1 against the version in place at that point to derive
concretely what the missing step needs to elicit and produce.

This also explains the "Goals aren't enumerated in Intent.md" weakness that showed up unresolved across all three
Intent Review passes: `Intent.md` is written by someone outside the process, at "idea" altitude, with no reason to
think in Goals/Users/Constraints vocabulary unless the presenter happens to. That's evidence the gap is structural,
not a defect in any one draft of `Intent.md`.

Status: open, approach chosen, not started.
