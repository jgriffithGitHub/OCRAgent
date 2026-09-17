# Engineering Intent Document Review

Reviewed document: `docs/Intent.md`
Review date: 2026-09-17
Produced using: `prompts/IntentReviewPrompt.txt`

## Overall Assessment

This is a genuinely strong first draft -- stronger than most intent documents get on the first pass. It states its core differentiator ("this can't be trusted," not just a raw confidence number) once, clearly, and never muddies it. Its "Out of Scope" section does real work by explaining *why* a boundary exists rather than just asserting it. The weak spot is that the document's own central claim doesn't yet reach all the way down to a behavior: it says the tool will know what it doesn't know, but never says what the tool actually *does* when it doesn't know something. That, plus an explicit "no non-functional requirements" line that's ambiguous about whether it means "decided out of scope" or "not written yet," are the two things worth resolving before this drives Requirements.md further.

## 1. Does It Express the Idea Clearly?

### Strengths
The Problem Statement grounds the whole document in a concrete example (a "pay now" letter reading differently depending on who sent it) before it ever gets abstract, and the OCR pipeline explanation (characters -> words -> paragraphs/tables, with positional context mattering) is written so a non-specialist could follow it. The differentiator sentence -- other products report confidence, none report "this can't be trusted" -- is the clearest, least hedged sentence in the document, which is exactly right given it's the most important one.

### Weaknesses
The letter example illustrates that context matters but doesn't quite close the loop on *how* structural recognition gets you from "there's a header and a closing" to "this is from Collections, not Customer Service" -- a reader has to infer the mechanism. Separately, there's a scattering of typos throughout (extacting, threshholds, capabilty, consumning, selecteable, "it ust be verified") -- none obscure meaning, but this is the document everything else derives from, so it's worth a clean pass.

## 2. Does It Separate Vision from Implementation?

### Strengths
Core Capabilities is written entirely tool-agnostic -- "accepts a PDF and extracts structure, data and extraction confidence" never names a library, model, or language. That's exactly the right altitude for an intent document.

### Weaknesses
The Security section breaks that discipline: it names PaddleOCR and Ollama specifically ("A prototype of this product was built using PaddleOCR and a model hosted by Ollama... if they are used it must be verified..."). The underlying requirement -- no exfiltration of extracted content -- is legitimately vision-level and belongs here. The specific tool names don't; they read like an implementation decision leaking into the vision document. (This is already acknowledged elsewhere as a deliberate deviation -- Requirements.md's C-2 -- but Intent.md itself doesn't flag it as a deviation, it just states it as fact.)

## 3. Does It Identify Users, Goals, and Constraints Clearly?

### Users
Clearly and correctly framed: this is consumed by other applications, not people directly, though its output is ultimately read by people. That distinction is stated once and never contradicted. What's left unstated is *what kind* of consuming application is the realistic primary case -- a third-party integrator, or (given this project's own origin story) another of Jeff's own agentic pipelines needing an internal tool call. That's not a flaw exactly, but it's the kind of detail that would sharpen the eventual interface-contract work (already tracked as an open gap elsewhere).

### Goals
Goals are present but not enumerated -- they're scattered across Problem Statement, Core Capabilities, and Success Criteria rather than listed as goals. A reader can reconstruct them (accurate extraction, calibrated confidence, inferred structure when no form exists, page-grouped output), but has to do that reconstruction themselves.

### Constraints
The strongest section in the document. The "paragraph grouping is context-blind by design" constraint is stated and explained. The no-exfiltration constraint is stated. But `"-Ilities": Non[e]` is a real gap dressed up as a decision -- it reads as "no non-functional requirements exist for this project," which would be an unusual thing to actually mean (no performance expectation at all? no reliability target at all?) versus the more likely reality, "not addressed yet." The document doesn't say which.

## 4. Does It Turn Business Needs into Software Direction?

### Strengths
Core Capabilities is concrete enough to build from directly: table data organized by row, bulleted/numbered content collected into arrays, consecutive text lines collected into paragraphs. These are testable behaviors, not aspirations.

### Weaknesses
The single most consequential business need in the document -- "know what it doesn't know" -- has no stated output behavior. "When extraction confidence thresholds are met, data is returned in a structured form" tells you what happens on success; it never says what happens on the *failure* of that threshold, which is the exact case the whole product exists to handle well. Does it return nothing? A partial structure with fields flagged? An error? Right now the doc's central value proposition and its actual output contract don't meet.

## 5. Does It Avoid Ambiguous Project Requests?

### Specific Ambiguities
"The trust threshold must be selecteable" doesn't say by whom or through what mechanism (a config value, a per-call parameter). "Measuring that against threshholds provided by the consuming application" (plural "thresholds," and two named axes -- structure recognition vs. data capture, a sentence earlier) leaves it unclear whether there's one threshold or two independently tunable ones. The medical-history example ("even a single missing data item is important and must be investigated") introduces a plausible regulated-data use case in passing, but nothing elsewhere in the document -- including Security, which only discusses network exfiltration -- addresses PHI-adjacent handling, retention, or compliance. If that's a real target use case rather than just a vivid example, it has requirements consequences that aren't reflected anywhere else in the doc.

### What Works
Out of Scope is doing real work here, and it's the part of the document I'd point to as a model for the rest: "record structure input support is deferred to v2" is a clean boundary, and the context-blind-paragraph constraint is stated *with its reasoning*, not just asserted. That combination -- a boundary plus why it's there -- is what makes a constraint usable downstream instead of just a rule someone has to take on faith.

---

## Summary of Recommendations

| Priority | Recommendation |
|---|---|
| High | State the output contract for the low-confidence case explicitly -- what the tool actually returns when its own core differentiator fires. This is the biggest gap between the document's stated value and its buildable direction. |
| High | Resolve `"-Ilities": None` -- say explicitly whether no NFRs is a real decision or a placeholder for "not written yet." Those lead to very different Requirements.md sections. |
| Medium | Clarify whether "trust threshold" is one value or two independent ones (structure confidence vs. data-capture confidence). |
| Medium | Decide whether regulated document types (the medical-history example) are actually in scope; if so, Security needs a privacy/compliance statement beyond network exfiltration. |
| Medium | Move the PaddleOCR/Ollama naming out of Security's vision-level requirement into a Requirements constraint or ADR, so Intent.md stays implementation-agnostic throughout, not just in Core Capabilities. |
| Low | Clean up the scattered typos (extacting, threshholds, capabilty, consumning, selecteable). |
