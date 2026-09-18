# Engineering Intent Document Review

Reviewed document: `docs/Intent.md`
Review date: 2026-09-17 (second pass, same day -- reworked after IntentReview-2026-09-17.md)
Produced using: `prompts/IntentReviewPrompt.txt`

## Overall Assessment

This rewrite closes the biggest gap from the first pass cleanly: the document now states a full, concrete output contract (always return what's obtainable, tag it against the caller's threshold, include per-field confidence, field count, and extraction method) where before there was none. The threshold ambiguity (one value vs. two axes) is also resolved -- it's explicitly one number now, precisely defined. What's still open: the aggregation method behind that one number (a sum, not an average, which behaves inconsistently across documents with different field counts), the regulated-document question from the first pass (unchanged), and the `"-Ilities"` section didn't get answered so much as removed, which trades an ambiguous answer for no answer at all.

## 1. Does It Express the Idea Clearly?

### Strengths
The Problem Statement now walks through an explicit three-step decomposition (extract characters -> cluster into groups -> infer structure), which gives the rest of the document a spine to hang off of. The bank-statement-vs-medical-history contrast is more mechanistic than the previous letter example: it doesn't just illustrate that context matters, it shows *how* confidence requirements differ by use case, which is exactly what the field-level confidence design in Core Capabilities needs to justify itself.

### Weaknesses
The document-type-recognition disclaimer (explicitly out of scope, but a consuming application with extra context can infer it from this tool's clustering output) is doing real scoping work but is packed into one dense paragraph a reader could skim past. New typos from the rewrite: "confindence" (Problem Statement), "it ma not be concerned" (should be "may"), "envelop" (should be "envelope"). Two typos carried over unchanged from the last pass: "capabilty" and "consumning" application, both in Security.

## 2. Does It Separate Vision from Implementation?

### Strengths
Real improvement: the PaddleOCR/Ollama mention in Security is now explicitly framed as "an example of this risk (and an example of what to look for in the chosen technology)" rather than stated as settled fact. That's the right way to name specific tools in a vision document -- clearly cautionary/illustrative, not a commitment.

### Weaknesses
Minor and arguably not a real weakness: Core Capabilities now reports "an indicator of the extraction method (e.g. 'visual' ... 'digital')" per item. That's borderline implementation detail, but it's defensible as a business-level distinction the consuming application genuinely needs (it bears directly on trustworthiness, the product's core differentiator), not a leaked implementation choice. Flagging it so it's a deliberate call rather than an accident.

## 3. Does It Identify Users, Goals, and Constraints Clearly?

### Users
Tightened and still clear: integrated into other applications, not used directly by people. One thing worth checking: the previous version's clarifying line that the tool's output still ultimately gets *read* by people is gone in this rewrite -- not a new ambiguity, but worth confirming that was an intentional trim and not a dropped sentence.

### Goals
Unchanged from the last pass: still reconstructable from Problem Statement + Success Criteria rather than enumerated. Not a new issue, just still open.

### Constraints
Improved. The context-blind-paragraph constraint moved from Out of Scope into Core Capabilities, which is the better home for it (it's a live operating behavior, not deferred work). A new, clearly testable constraint appeared: the consuming application *must* provide an acceptable extraction score -- not optional. The `"-Ilities"` section, which the last review flagged as an ambiguous "None," is gone entirely now rather than resolved -- see Overall Assessment.

## 4. Does It Turn Business Needs into Software Direction?

### Strengths
This is where the rewrite earns its keep. The single biggest gap from the last review -- what happens when confidence is low -- now has a complete, buildable answer: always return everything obtainable, flag it against the caller's threshold, include per-field confidence scores, a total recognized-field count, and an extraction-method tag. That is a real output contract, not an aspiration.

### Weaknesses
The threshold itself -- "the minimum allowed value for the sum of all field confidence values" -- is a **sum**, not an average or a per-field minimum. The same threshold number means something different depending on how many fields a document has: 20 fields at 90% each sums far higher than 3 fields at 90% each, even though both represent identically reliable extractions. The medical-history example a few paragraphs earlier describes "95% confidence on all fields," which reads like a per-field minimum, not a sum -- the two ideas sit close together in the document without quite agreeing with each other. Worth a second look before this becomes a formula in Requirements.md.

## 5. Does It Avoid Ambiguous Project Requests?

### Specific Ambiguities
The sum-vs-average aggregation question above. Regulated-document handling is still open -- the medical-history example remains, but Security still covers only network exfiltration, not retention, PHI, or compliance; unchanged from the last pass. And the `"-Ilities"` section's removal is itself ambiguous: is NFR content being deliberately deferred to `docs/Requirements.md` in full, or did a placeholder just not make it into the rewrite? The document doesn't say.

### What Works
The three-problem decomposition at the top gives the whole document a visible spine -- Core Capabilities and Success Criteria both map back to it in a way the previous version's more independently-written sections didn't. That's a genuine structural improvement, separate from any individual content fix.

---

## Summary of Recommendations

| Priority | Recommendation |
|---|---|
| High | Confirm whether summing (not averaging) field confidence scores for the "acceptable extraction score" is intentional -- as written, the same threshold behaves differently depending on field count per document, and it doesn't quite match the "95% on all fields" framing used earlier in the same document. |
| Medium | State explicitly whether NFRs are being deferred entirely to `docs/Requirements.md` (dropping `"-Ilities"` on purpose) or still need a placeholder here -- right now it reads as silently missing rather than a stated decision. |
| Medium | Regulated-document handling (the medical-history example) still has no Security-section counterpart beyond network exfiltration -- same open item as the last review. |
| Low | New typos from the rewrite: "confindence," "it ma not," "envelop" (envelope) -- plus carried-over "capabilty," "consumning" in Security. |
