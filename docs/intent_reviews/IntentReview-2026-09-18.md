# Engineering Intent Document Review

Reviewed document: `docs/Intent.md`
Review date: 2026-09-18 (third pass, following the 2026-09-17 second pass)
Produced using: `prompts/IntentReviewPrompt.txt`

## Overall Assessment

Clean sweep of every open item from the second-pass review. The sum-vs-average threshold question now has a full, worked-example answer -- and it's a better answer than what the last review even suggested: pairing the sum with a per-field minimum threshold catches exactly the failure mode (one missed field hiding inside a high aggregate score) that a plain average wouldn't have caught either. The `"-Ilities"` ambiguity is resolved with an explicit "not known at this time, expected to grow" statement instead of silence. The regulated-document/PII question now has a real answer: this component doesn't retain data and pushes PII handling to the consuming application, with the reasoning stated (it has no context about what kind of data it's given). Every typo flagged in the last two passes is fixed. What's left is minor: one unclosed parenthesis, a couple of small grammar slips, and one spot where a definition gets refined mid-paragraph in a way that reads as two different things on a first pass even though the underlying logic is consistent.

## 1. Does It Express the Idea Clearly?

### Strengths
The new confidence-math section is the strongest addition in this pass: it states the problem (a high aggregate score can hide a fully-missed field), walks a concrete worked example (10 expected fields, 85% per-field bar, 9 fields at 100% plus one complete miss = a 90% sum that would wrongly pass an 85% aggregate check), and then explains *why* the design stops short of an average rather than just asserting the choice ("the average is not providing new information... the consuming application can compute it from the data returned"). That's reasoning shown, not just a conclusion stated -- exactly what the last two reviews were asking for more of.

### Weaknesses
The "number of fields recognized" count is introduced once in the Problem Statement meaning "anything successfully extracted," then refined two paragraphs later to also exclude fields below the per-field threshold ("that field would not be counted... but not included in the count"). Read straight through, the logic holds together, but a reader skimming either paragraph alone could walk away with two different definitions of the same count. Worth collapsing into one explicit definition when this becomes Requirements.md language, even though nothing here is actually contradictory.

## 2. Does It Separate Vision from Implementation?

### Strengths
Still solid -- Core Capabilities stays behavior-focused (what gets returned and why), and the PaddleOCR/Ollama mention in Security remains framed as a cautionary example rather than a commitment, same as the last pass.

### Weaknesses
"Accepts a PDF passed as a byte array" is a data-type-level statement, which sits closer to an interface spec than a vision statement. It's defensible here -- it's really a scope decision (single page only, multi-page splitting is the caller's job, and *why* that side-steps a real problem -- how would a 600-page PDF even get passed in) more than an implementation choice, so I'd call this a judgment call worth confirming rather than a clear violation.

## 3. Does It Identify Users, Goals, and Constraints Clearly?

### Users
Meaningfully improved: Primary Users now gives three concrete example use cases (document format specification, customer-service key-value lookups, summarization-plus-presentation) instead of just "integrated into other applications." Still deliberately open-ended about which is primary, which reads as intentional rather than missing.

### Goals
Same as the last two passes -- still reconstructable from Problem Statement and Success Criteria rather than enumerated. Not a new issue.

### Constraints
Substantially stronger. Three new constraint-bearing sections landed: Performance (no formal spec, but an honest anecdotal number -- up to a minute per page depending on format and hardware), Security (no data retention, PII handling pushed to the consuming application, with reasoning), and "Other NFRs" (explicitly "not known at this time," resolving the ambiguity the last review flagged about the missing `"-Ilities"` section). The per-field-vs-overall threshold pair is now also a stated, required input from the consuming application, not just an aggregate.

## 4. Does It Turn Business Needs into Software Direction?

### Strengths
This is now a complete loop: the differentiator (know what you don't know) has a stated output contract (always return what's found), a stated aggregate signal (the sum-based score), a stated per-field signal (the minimum threshold and its filtered count), and a worked example showing why both are needed together. That's about as buildable as an intent document gets before it becomes a formal spec.

### Weaknesses
None significant this pass -- see the mid-paragraph definition point under Section 1, which is a clarity issue more than a direction issue.

## 5. Does It Avoid Ambiguous Project Requests?

### Specific Ambiguities
Two small textual issues, not conceptual ones: the Constraints sentence in Core Capabilities opens a parenthesis after a semicolon and never closes it ("...text block; (a group of lines of text... does not have the context to make that call." -- no closing `)`), and "This application provides a capability that, must be hosted by a consuming application" has a stray comma that changes how the sentence reads on a first pass.

### What Works
The willingness to explain a design choice by first showing why the *simpler* choice (a plain average) doesn't fully solve the problem is the strongest pattern in this revision, and it shows up twice -- once for the sum-vs-average question, once implicitly in the PII section (explaining why this component *can't* make PII judgments itself, rather than just declaring PII out of scope). That reasoning is what makes both of those constraints usable downstream instead of just assertions to take on faith.

---

## Summary of Recommendations

| Priority | Recommendation |
|---|---|
| Medium | Close the unclosed parenthesis in Core Capabilities' Constraints sentence -- as written it will read as a formatting error to anyone parsing this into Requirements.md. |
| Low | "This application provides a capability that, must be hosted..." -- stray comma, minor grammar cleanup. |
| Low | "blocks of lines will be a presented as a 'paragraph'" still has the stray "a" that's been in this sentence since the first draft -- worth catching now that everything else got a clean typo pass. |
| Low | Collapse the "number of fields recognized" definition (introduced one way, refined a different way two paragraphs later) into a single explicit statement when this becomes Requirements.md language. |
