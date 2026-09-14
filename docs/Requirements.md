# OCRAgent — Software Requirements (Draft v1)

**Source document:** `docs/IntentStatement.txt`
**Status:** Draft — derived directly from the intent statement. Sections marked with `> GAP:` identify places where the intent document does not provide enough information to state a testable requirement; an assumption was **not** substituted for these. See the consolidated gap list at the end.

---

## 1. Functional Requirements

**FR-1 — PDF ingestion**
The system shall accept a PDF file as input for processing.

**FR-2 — Structure extraction**
The system shall extract, for each recognized data item on a page, its location and its relationship to other data items near it ("structure").

**FR-3 — Data extraction**
The system shall extract the textual/data content of each recognized data item on a page.

**FR-4 — Confidence reporting**
The system shall extract and report a confidence value associated with the extraction of each recognized data item.

**FR-5 — Confidence-gated structured output**
When a data item's (or record's) extraction confidence meets a defined threshold, the system shall return that data in structured form.

**FR-6 — Explicit "cannot be trusted" judgment**
When confidence does not meet the threshold in FR-5, the system shall not silently omit or silently guess the value. It shall return an explicit statement that the extracted content "cannot be trusted," distinct from a normal confidence score, for the affected item(s).

**FR-7 — Form-based record structure (when a form is present)**
If the input document is a recognized form, the system shall return extracted data organized according to that form's structure.

**FR-8 — Inferred record structure (when no form is present)**
If the input document is not a recognized form, the system shall infer a record structure using location-clustering of the extracted items.

**FR-9 — Table row grouping**
The system shall organize data recognized as being part of a table by row, based on shared bounding coordinates (e.g., items sharing the same top/bottom bounds belong to the same row).

**FR-10 — List grouping**
The system shall collect content recognized as a bullet list or numbered list into an array structure, preserving list order.

**FR-11 — Paragraph grouping**
The system shall collect consecutive lines of body text into a "paragraph" grouping.

**FR-12 — Paragraph grouping is context-independent**
Per the stated constraint, paragraph grouping (FR-11) shall be applied purely on the basis of line adjacency/positioning, regardless of what the paragraph's semantic role might be (e.g., an address block and a block of reference data are both grouped as "paragraphs" the same way).

**FR-13 — Page-level grouping**
The system shall group all output (data, structure, confidence) by page, and, within a page, by the related structure identified above (table rows, lists, paragraphs).

**FR-14 — Programmatic (agent-facing) interface**
The system shall expose its input/output through a machine-consumable interface suitable for invocation by other software agents, not through a human-facing UI.
> GAP: see Gap List item G-1 — the intent document does not specify what that interface is (CLI with file I/O, REST/HTTP API, Python library/importable function, MCP tool, message queue, etc.), nor its request/response schema.

---

## 2. Non-Functional Requirements

> GAP: The intent document does not state any non-functional requirements directly. The items below are the categories a requirements document of this kind would normally need populated, listed here specifically so they can be confirmed or filled in — none of the numeric targets or choices below are assumed; each is flagged.

**NFR-1 — Performance / latency**
> GAP: see Gap List item G-2 — no target processing time per page/document, no target throughput (pages/hour, documents/hour), and no statement of whether processing is expected to run synchronously (caller waits) or asynchronously (batch/queued).

**NFR-2 — Scalability / batch volume**
> GAP: see Gap List item G-3 — the earlier working name "batch data extraction agent" implies multi-document batch processing, but the intent statement describes single-PDF input only. Expected batch sizes, concurrency, and whether batching is in scope for this version are not stated.

**NFR-3 — Environment / deployment**
> GAP: see Gap List item G-4 — no statement of target OS, whether local-only execution is required (vs. cloud/server deployment), whether GPU is required or optional, or how the OCR/LLM components are expected to be packaged (matches the current prototype's local PaddleOCR + local Ollama LLM approach, but the intent document itself is implementation-silent, and per the user's own note this is a known, accepted deviation from spec-first ordering).

**NFR-4 — Accuracy / quality**
The system's central non-functional quality attribute, per the problem statement, is that reported confidence must be trustworthy: it is more important that the system correctly identify when it does *not* know something than that it maximize raw extraction accuracy.
> GAP: see Gap List item G-5 — no target accuracy rate, no target false-trust rate (cases where the system reports confidence but the extraction is actually wrong), and no defined confidence scale (0–1 float? categorical high/medium/low? something else) or threshold value(s) for FR-5/FR-6.

**NFR-5 — Language / document type support**
> GAP: see Gap List item G-6 — no statement of supported languages, document types (letters, forms, tables, invoices, etc. — the problem statement uses "letters" only as an illustrative example), page size/orientation limits, or handling of multi-page documents beyond "group by page."

**NFR-6 — Security / privacy**
> GAP: see Gap List item G-7 — no statement about data handling, retention, or confidentiality, despite the tool processing arbitrary (possibly sensitive) document content on behalf of another agent.

**NFR-7 — Reliability / error handling**
> GAP: see Gap List item G-8 — no statement of expected behavior for inputs the system cannot process at all (corrupt PDF, encrypted PDF, non-PDF file, zero-page PDF, scanned-image-only PDF with no extractable content, etc.), separate from the "low confidence" case already covered by FR-6.

**NFR-8 — Observability / logging**
> GAP: see Gap List item G-9 — no statement of logging, auditability, or traceability requirements (relevant since a calling agent — not a person — may need to debug or audit results).

**NFR-9 — Portability / maintainability**
> GAP: not addressed in the intent document; flagged only because it is a standard category. May reasonably be deferred to a design-phase document rather than requirements.

**NFR-10 — Cold-start network isolation (validated, not yet proven)**
The system's OCR and LLM components shall not depend on outbound network access to produce output, and shall not transmit document content off the local machine, in any deployment where that is a stated requirement (see NFR-6/G-7).
> STATUS: This is currently an *intent*, not a verified requirement. A warm-cache, network-connected manual check (2026-09-13 — see Section 8, Investigation Findings) observed only loopback traffic between `testAgent.py`, Ollama, and its inference backend, with no connections to any external host. That check is not sufficient to claim this requirement is met, for two reasons: (1) it did not test a cold start — the PaddleX model cache was fully warm the entire time, and published upstream issues describe PaddleX contacting external model-hosting platforms (huggingface.co, modelscope.cn, aistudio.baidu.com, bcebos.com) specifically around cache/model-availability checks, a code path a warm-cache run may not fully exercise; and (2) snapshot-based tools (Task Manager, Resource Monitor, TCPView) can miss a connection attempt that is brief, fails fast, or falls between polling intervals.
> ACTION REQUIRED (do not lose this): before this requirement can be marked verified, run a **cold-start test**: clear or relocate the local PaddleX/PaddleOCR model cache (and, as a second variant, fully disconnect/firewall the machine from the internet) and rerun `testAgent.py` from that clean state while capturing traffic with a packet-level tool (e.g., Wireshark) on both the loopback and physical/Wi-Fi adapters, not just a connection-snapshot tool. Create a task (under `tasks/`) and a corresponding test (under `tests/`) for this specific scenario so the result is reproducible and documented, and so the eventual NFR-6/NFR-10 language can state a precise, evidence-backed scope (e.g., "no outbound calls occur once models are cached" vs. "no outbound calls occur under any condition" — these are different claims and the intent document does not yet say which one is required).

---

## 3. Business Rules

**BR-1** A confidence threshold governs whether extracted data is returned as structured output (FR-5) or flagged as untrustworthy (FR-6). The specific threshold value(s) are not defined in the intent document.
> GAP: see Gap List item G-5.

**BR-2** Record structure is determined in one of exactly two ways: (a) a recognized form's known structure, when the input document is a form, or (b) inferred location-clustering, when it is not.
> GAP: see Gap List item G-10 — how the system determines whether a document "is a form" (and by extension which branch of BR-2 applies) is not defined.

**BR-3** Table rows are defined by shared horizontal (top/bottom) bounding coordinates among content blocks.

**BR-4** Paragraph grouping is applied uniformly by line-adjacency and does not attempt to resolve or assert the semantic role of the text block (BR follows directly from the stated Constraint). This is a deliberate business rule, not a limitation to be fixed later.

**BR-5** Version 1 of this system is a one-way extraction tool: it does not accept a caller-supplied target record structure to conform its output to. That capability is explicitly deferred to a future version (see Out of Scope, Section 6).

**BR-6 — Explicit-requirement gate for security/architecture-relevant findings**
Any requirement whose failure mode is data exfiltration, unauthorized network access, or credential exposure shall not be considered satisfied until it has an explicit, named acceptance criterion and a passing, recorded test result against it. A requirement in this category with no such test is an open gap, not an assumed pass.

This rule exists to close a specific seam identified while adapting Gem Iroko's Spec-Driven AI Engineering process to this project: that process (like many) leans on an organization's existing governance — e.g., a standing "always seek Security and Architecture Review approval" instruction that might otherwise live in an agent-instructions file such as `CLAUDE.md`/`AGENT.md`. That kind of instruction is real, but it is process guidance about *how the work gets done*, is organization- and tool-dependent, and isn't independently testable. BR-6 instead states the gate as a property of the requirements themselves — portable across organizations, tools, and reviewers — while still guaranteeing the same outcome: nothing security-relevant ships on the strength of an untested assumption.

**BR-6 is already in force**: NFR-10 (cold-start network isolation) is its first governed case. NFR-10's "runs locally" claim was tested only under warm-cache, snapshot-tool conditions (see Section 8, Investigation Findings) and therefore does not yet have the acceptance criterion and passing test BR-6 requires — it remains an open gap (G-14) until the cold-start test described in NFR-10 is run and recorded.

---

## 4. Permissions

> GAP: see Gap List item G-11 — the intent document contains no information about permissions, authentication, authorization, or access control of any kind. Given that "primary users… will be other agents, not people," this section cannot be populated without further input: for example, whether any agent that can invoke the tool may do so (no auth), whether calling agents must be authenticated/authorized, whether there are per-agent rate limits or quotas, and whether the tool needs to restrict what documents/paths it may read (e.g., sandboxing, since it's invoked by other automated agents rather than a supervised human).

---

## 5. Constraints

**C-1** Paragraph grouping shall always be presented as a "paragraph" regardless of overall document context, because the system cannot be certain of a text block's true semantic context (e.g., a block of lines at the top of a document might be an address or might be reference data). This is a stated, accepted limitation, not a defect. *(restates the intent document's Constraints section verbatim as a formal constraint; see also BR-4.)*

**C-2** The implementation approach (Python, PaddleOCR for OCR, a locally hosted LLM via Ollama for semantic labeling) has already been selected, ahead of the normal sequencing of the Spec-Driven AI Engineering process (which calls for implementation choice after requirements are finalized). This is an acknowledged, deliberate deviation for this project, not an oversight, and this requirements document does not attempt to retroactively justify or re-derive the implementation choice — it treats the choice as a known constraint going forward.
> GAP: see Gap List item G-12 — it is not yet stated whether this requirements document should be written to be implementation-agnostic (as if the tool choice weren't fixed) or should explicitly incorporate the known implementation constraints (e.g., "runs locally," "no reliance on paid cloud OCR/LLM APIs") as first-class constraints.

---

## 6. Out of Scope (from intent document, restated for completeness)

- Accepting a caller-supplied target record structure and conforming output to it — explicitly deferred to "Version 2."

---

## 7. Acceptance Criteria

The intent document's own "Success Criteria" is stated as a guiding principle ("this tool must know what it does not know") rather than as measurable, testable acceptance criteria. Below is a best-effort translation into testable form, staying strictly within what the intent document actually asserts. Numeric thresholds are intentionally left as placeholders — see Gap List item G-5.

**AC-1** Given a PDF with clearly legible, unambiguous content, when the system processes it, then every extracted data item is returned with (a) its extracted value, (b) a confidence score, and (c) its structural grouping (page, and paragraph/row/list membership as applicable).

**AC-2** Given a PDF (or region of a PDF) whose content cannot be reliably recognized, when the system processes it, then the affected item(s) are explicitly flagged as untrustworthy — not silently omitted, and not filled in with a best-guess value presented as if it were reliable.
> GAP: this is the most important behavior in the entire intent document (it is the named differentiator vs. other products) and it currently has no measurable pass/fail definition — see Gap List item G-5 for the missing threshold, and G-13 below for a missing example/worked scenario.

**AC-3** Given a PDF that is a recognized form, when the system processes it, then output record structure matches the form's known structure (FR-7).

**AC-4** Given a PDF that is not a recognized form, when the system processes it, then output record structure is inferred from location-clustering (FR-8), and paragraph/list/table groupings follow BR-3/BR-4/FR-9/FR-10/FR-11 exactly.

**AC-5** Given any input PDF, when the system produces output, then that output is grouped first by page, and second by the structural relationships defined above (FR-13).

**AC-6** Given a request from a calling agent, when the system responds, then the response is consumable programmatically without human interpretation (FR-14).
> GAP: cannot be made fully testable until G-1 (interface/schema) is resolved.

---

## 8. Investigation Findings — Network Activity (2026-09-13)

This section records a manual investigation triggered by observed network activity while running `testAgent.py`, kept here so the evidence and its limits aren't lost between requirements-refinement passes.

**Trigger:** Jeff noticed network activity in Task Manager while `testAgent.py` was running and asked whether PaddleOCR or Ollama was responsible, and what it implied for a tool intended to run locally.

**Research finding (not yet confirmed against this machine):** Multiple PaddlePaddle/PaddleOCR GitHub issues (PaddleX #4578; PaddleOCR #16620, #16639) document that PaddleX's OCR pipeline initialization attempts to contact four external model-hosting platforms — `huggingface.co`, `modelscope.cn`, `aistudio.baidu.com`, and `paddle-model-ecology.bj.bcebos.com` (Baidu's CDN) — as part of a model-availability check, in some cases even when a valid local model cache already exists, with at least one report of no working environment-variable override to fully suppress the check. Separately, Ollama on Windows runs a background auto-updater (`ollama.com/api/update`) unrelated to inference itself.

**Empirical finding (this machine, warm cache, 2026-09-13):** Jeff captured live network state during two `testAgent.py` runs using Windows Task Manager (Performance tab, per-adapter throughput), Resource Monitor (Network tab — Processes with Network Activity, TCP Connections, Listening Ports), and Sysinternals TCPView. Across both runs, every PaddleX model referenced by the pipeline reported "Model files already exist. Using cached files." with no download activity. The only TCP activity attributable to the OCR/LLM stack was `python.exe` (testAgent.py) ↔ `ollama.exe` ↔ `llama-server.exe`, entirely over loopback (`127.0.0.1` / `::1`, port 11434 and ephemeral ports). No connection to `huggingface.co`, `modelscope.cn`, `aistudio.baidu.com`, or `bcebos.com` appeared in any capture. (A "kubernetes.doc…" label seen in Resource Monitor was confirmed to be a reverse-DNS display name for the loopback address, not a distinct remote host.) Other network activity visible in the same captures — `claude.exe` (the Claude desktop app), `multipass.gui.exe`/`multipassd.exe` (Canonical Multipass), `postgres.exe`/`pgagent.exe` (a local Postgres instance), `SpotifyLauncher.exe` (Spotify) — was confirmed unrelated to `testAgent.py`.

**Conclusion, scoped precisely:** With a fully warm model cache and normal internet connectivity, the OCR+LLM pipeline in this test produced no observed outbound traffic to any external host. This is real evidence, but it is a *warm-cache* result obtained with *snapshot-based* tools, not a *cold-start* result obtained with a *packet-capture* tool — so it does not yet confirm or refute the upstream-documented cold-cache/offline behavior. See NFR-10 for the follow-up test this implies, and G-14 in the gap list below.

---

## Consolidated Gap List

These are the specific points where `docs/IntentStatement.txt` does not currently provide enough information to finalize the corresponding requirement(s) above. Nothing in the numbered sections above assumes an answer to these — each was left as an open placeholder or a restated constraint instead.

| # | Gap | Affects |
|---|-----|---------|
| G-1 | No defined interface/API contract for how another agent invokes this tool and what the request/response payload looks like (protocol, schema, sync vs. async). | FR-14, AC-6 |
| G-2 | No performance/latency targets (per-page or per-document processing time; synchronous vs. queued). | NFR-1 |
| G-3 | "Batch" was used earlier as a working description of this tool, but the intent document describes single-PDF input only — unclear if multi-document batch processing is in scope for this version. | NFR-2 |
| G-4 | No stated deployment/environment requirements (OS, local vs. server/cloud, GPU requirement, packaging). | NFR-3, C-2 |
| G-5 | No defined confidence scale, no defined threshold(s) separating "trusted" output (FR-5) from "cannot be trusted" output (FR-6), and no target accuracy/false-trust rate. This is the single most consequential gap, since it underlies the tool's core differentiator. | FR-5, FR-6, BR-1, NFR-4, AC-1, AC-2 |
| G-6 | No stated supported languages, document types, page sizes/orientations, or explicit multi-page handling beyond "group by page." | NFR-5 |
| G-7 | No stated data handling/retention/confidentiality requirements for (potentially sensitive) document content. | NFR-6 |
| G-14 | The intent document doesn't say whether "runs locally" (implied by the chosen implementation, C-2) means "no outbound network calls once models are cached" or the stricter "no outbound network calls under any condition, including cold start." These are different, both currently plausible, and only a cold-start test (not yet run) can show which the current implementation actually satisfies. | NFR-10, NFR-6 |
| G-8 | No defined behavior for inputs the system cannot process at all (corrupt/encrypted/non-PDF/empty file), as distinct from low-confidence extraction. | NFR-7 |
| G-9 | No stated logging/auditability/traceability requirements. | NFR-8 |
| G-10 | No stated method for how the system determines whether an input document "is a form" (which selects between BR-2's two branches). | BR-2, FR-7 |
| G-11 | No permissions/authentication/authorization/access-control information at all, despite the stated agent-to-agent usage model. | Section 4 (entire) |
| G-12 | Not yet confirmed whether this requirements document (and the design phase that follows it) should be written implementation-agnostic, or should formally incorporate the already-chosen implementation (Python/PaddleOCR/local LLM) as a constraint. | C-2 |
| G-13 | No worked example/scenario of a "cannot be trusted" judgment (e.g., what the output object looks like for a low-confidence item), which would make AC-2 concretely testable. | AC-2 |

---

*Prepared as a first-pass translation of `docs/IntentStatement.txt` into structured requirements. Expected to be revised iteratively as the intent document is refined to close the gaps above.*
