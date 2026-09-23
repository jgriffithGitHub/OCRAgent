---
# Product Requirements Specification — Mapping Skill
**Status:** Draft v0.5 — 2026-09-22 (v0.5: the path is one-way, document to artifacts (BR-005); reference outputs for SBC_Example_Data (annotated PDF and a partly completed workbook) added as the acceptance fixture; `Shared Content` column added; the workbook is the analyst's working document once handed over (OQ-16, OQ-17 resolved). v0.4: boxes are read from each item's four corners instead of derived from row heights (FR-BOX-001, BR-004; Structure OQ-22). v0.3: split-row and merged-cell test cases added (FR-BOX-003); named Mapping, no confidence values (OQ-10, OQ-12); form controls numbered and boxed (FR-ITEM-001, OQ-9); always runs after DocExtractor and the Structure skill (OQ-7, LIM-002); barcode boxes taken from the retained extraction record and defined as locator tags, not sizes (FR-BOX-002, OQ-15); outputs tied to one PDF instance and versioned, `Location` column added (FR-VER-001/002, OQ-5 resolved); `Mixed text sizes` column added (FR-MIXED-001); OQ-2 and OQ-11 resolved; the manual step after this skill, and why it leads to Dynamic Data, described in §0; c4.json added as the multi-page test case. v0.2: re-based on DocSpec `skills/specReview/SKILL.md` and `scripts/annotate.py`, the skill being replaced; items, numbering, boxes, workbook columns, and file names now specified; proposals from v0.1 that specReview does not support removed or moved to open questions. v0.1: first draft from DocExtractor_PRS.md Persona 3)
---

# Related Intent Document
**Intent Document:** [intent/Intent.md](intent/Intent.md)

# 0. Context

The Mapping skill is the third of the three components in this project:

1. **DocExtractor** (tool, [DocExtractor_PRS.md](DocExtractor_PRS.md)) — reports what a single PDF page *contains*.
2. **Structure skill** ([Structure_PRS.md](Structure_PRS.md)) — derives the layout and writes the `specScan` JSON.
3. **Mapping skill (this spec)** — numbers every leaf item in that JSON and produces two review artifacts for a person: an annotated PDF with a numbered box around each item, and a workbook with one row per item in which the person records whether the item is conditional or comes from external data.

**Origin.** This skill is the existing DocSpec skill `specReview` (`C:\Projects\DocSpec\skills\specReview\SKILL.md`, implemented by `scripts/annotate.py`). Unlike specScan, specReview already works from a spec rather than measuring the page, so it carries over largely unchanged. The changes are that its input now comes from the Structure skill, and it can use DocExtractor's barcode regions instead of searching the PDF for barcode images (FR-BOX-002).

The Mapping skill does not decide which items are data, and it does not find where data comes from. It creates the place where that information is recorded. Filling it in is a manual task a person performs after the skill runs: keeping the workbook open on the right row and the annotated PDF visible for context, while working with a DBA, database tools, and data catalogs to work out what to record. That task is tedious, and reducing it is the purpose of the **Dynamic Data** skill, a separate, future project (OOS-001).

# 1. Purpose & Scope

Given a PDF and one version N of its Structure JSON (`<name>.v<N>.json`), the Mapping skill writes:

- **`<name>_annotated.v<N>.pdf`** — a copy of the PDF with a numbered red box around every leaf item, and
- **`<name>_review.v<N>-0.xlsx`** — one row per numbered item, with the item's ID, page, location, and content, and blank columns for a person to complete.

All outputs belong to one PDF instance and are versioned (FR-VER-001).

In scope: numbering, box placement, drawing, and the workbook. Out of scope: running the Structure skill, deciding what any item means, and anything done with the completed workbook (§9).

# 2. Glossary / Ubiquitous Language

Terms from DocExtractor_PRS.md §2 and Structure_PRS.md §2 (including **leaf item**) have the same meaning here. **Field** remains reserved for the future Dynamic Data skill.

- **ID**: a positive integer identifying one leaf item, unique within the document.
- **box**: an unfilled red rectangle drawn around one leaf item on the annotated PDF.
- **label**: the ID printed in white on a small solid red block at the box's top-left corner.
- **annotated PDF**: `<name>_annotated.v<N>.pdf`, a copy of the input with boxes and labels drawn on it, generated from Structure JSON version N. The input is never changed.
- **review workbook**: `<name>_review.v<N>-<M>.xlsx`, one row per ID, generated from Structure JSON version N. M is 0 as generated and increases by one each time the analyst saves a revision.
- **PDF instance**, **version**: as in Structure_PRS.md §2.
- **analyst**: the person who completes the review workbook.

# 3. Users

## Persona 1: Analyst (primary)
- Role: a person reviewing a document so that it can be rebuilt in a document-generation system.
- Problem statement: needs every piece of content on the document numbered and located, with a place to record whether it is conditional or externally sourced, so that nothing is overlooked and the answer for each item can be traced to a spot on the page.

## Persona 2: Data owner / developer
- Role: the person who builds the data feed that supplies the document.
- Problem statement: needs to see which items the analyst marked as external data, and where each one is on the page.

## Persona 3: Dynamic Data skill (future)
- Role: the future skill that suggests which items are variable data.
- Problem statement: will need the same IDs, so that its suggestions land in the same rows. (Recorded so that this spec does not block it; no requirements here.)

# 4. User Stories

**US-001**: As an analyst, I want every leaf item, including each individual table cell, to have a numbered box, so that I can flag one checkbox option as conditional without flagging the whole grid.

**US-002**: As an analyst, I want a workbook row for each box with the item's text already filled in, so that I only record my decisions.

**US-003**: As an analyst, I want every ID label readable, even where items are packed together, so that I can match every row to its box.

**US-004**: As a data owner, I want to find box N on the annotated PDF from row N in the workbook, and the reverse.

# 5. External Interface

**IF-001 — Invocation**
The skill is invoked with a document name and, optionally, a Structure JSON version (default: the highest). `<name>.pdf` and `<name>.v<N>.json` (whose `fileName` is `<name>`) must both exist in the same folder. If either is missing, the skill stops and tells the caller which one, and that the Structure skill must run first. If the JSON's `source.sha256` does not match the PDF's bytes, the skill stops and says the JSON describes a different PDF instance (FR-VER-001). It does not run the Structure skill itself, and does not guess content or positions missing from the JSON.

**IF-002 — Outputs**
`<name>_annotated.v<N>.pdf` and `<name>_review.v<N>-0.xlsx`, written beside the inputs, where N is the Structure JSON version used. An existing file is never overwritten (FR-VER-001).

## 5.1 Review workbook

| Column | Filled by | Content |
|---|---|---|
| ID | skill | The item's number, matching its box |
| Page | skill | Page number (1-based) |
| Location | skill | The box's corners, in inches (e.g. `4.31in, 0.75in, 4.52in, 4.25in`). **Change from specReview:** added so that rows can be matched across versions by page and location when IDs shift (FR-VER-002) |
| Content | skill | The item's text; runs concatenated in order. `[Image: IMAGE001]`, `[Barcode]`, `[Rule]` for non-text items; `[Form control: <type>] <name> = <value>` for form controls (e.g. `[Form control: checkbox] topmostSubform[0].Page1[0].c1_1[0] = Off`), so the analyst sees both that it is a control and what it holds |
| Mixed text sizes | skill | `Yes` when the Structure output marks the item `mixed-heights: true` (sizes differ by more than 0.5 pt); otherwise blank (FR-MIXED-001) |
| Conditional? | analyst | `Yes` / `No` / `Unsure` (drop-down) — does the item appear only under certain conditions? |
| External Data? | analyst | Whether any part of the item comes from an external data source, and where from. In the SBC reference workbook the analyst writes the mapping itself, e.g. `DI00001 = /SBCData/PolicyStartDate` or a variable name such as `{SBCOADedAns}` |
| Shared Content | analyst | Content reused elsewhere, recorded as a reference and its value, e.g. `SC00001 = 1-888-428-2566` |
| Notes | analyst | Free text. In the reference workbook: `Page Number Code` on each page-number item, `Provided by customer provided PDF` on an image |

Rows are in ID order; the header row is frozen.

`Content` starts as the extracted text, where there is any. From handover it is the analyst's working column: in the SBC reference workbook the analyst has moved it toward what an author would implement, replacing variable spots with tokens (`Coverage Period: {{DI00001}} - {{DI00002}}`) and collapsing a long block of repeated language-assistance text to a summary with a note saying so. Each such change is a workbook revision (FR-VER-001).

A token such as `DI00001` or `SC00001` is a mapping point, a single symbol in the author's content standing for the XPath into the data model recorded beside it in `External Data?` or `Shared Content` — a kind of pseudo-code joining the two. The analyst creates and numbers them; the skill neither assigns nor interprets them (BR-001, OQ-17). A second sheet, `Version`, records: PDF file name, PDF SHA-256, Structure JSON version (N), workbook revision (M), origin (`mapping-skill` or `analyst`), and date.

## 5.2 Test corpus

Purpose-built specimens, each produced by four platforms, are specified in [TestSet_PRS.md](TestSet_PRS.md); S1 (split rows), S2 (merged cells), S6 (volume) and S7 (form controls) exercise this skill.

Structure_PRS.md §5.2, with each worked example's JSON as the input spec. **Reference outputs** exist for SBC_Example_Data: `SBC_Example_Data_annotated.pdf` and `SBC_Example_Data_review.xlsx`, the latter partly completed by an analyst (271 numbered items across 8 pages; 18 rows with external-data mappings, 10 notes, 1 shared-content entry). SBC_Example_Data exercises boxes for merged cells: a cell that spans rows is boxed over its full merged extent. PastDue_0001 exercises split rows across pages 2, 3, and 4. Leaf-item counts from the current JSON files: WorkedExample1 71, WorkedExample2 23, WorkedExample3 60, WorkedExample4 14, WorkedExample5 34. JanusSamples/c4 (6 pages; the reference c4.json has 89, 195, 153, 110, 86, 1 leaf items by page, but page 6 will change under Structure FR-OCRBG-001) is the multi-page case, specReview's untested condition.

# 6. Functional Requirements

**FR-ITEM-001 — What gets numbered**
The skill shall number every leaf item: each top-level `paragraph`, `listitem`, `image`, `barcode`, `rule`, and `form_control`, and every cell of every table (every entry in a row's `columns`, including empty cells). It shall not number a table or a row.
AC: Given WorkedExample4, When processed, Then 14 IDs exist.
AC: Given WorkedExample5, When processed, Then 34 IDs exist.
AC: Given WorkedExample1, When processed, Then 71 IDs exist. (specReview's notes say 69; the worked example is newer than the notes. OQ-11.)
AC: Given fw9.pdf, When processed, Then page 1 has 23 rows whose Content begins `[Form control:`, 15 of them `text` and 8 `checkbox`, each boxed at its control's bounding box and each showing its value.
AC: Given fw9_filled.pdf, When processed, Then the row for the control named `…f1_01[0]` shows `= PAT Q SAMPLE`.

**FR-NUM-001 — Numbering**
IDs shall be one sequence starting at 1 across the whole document (not restarted per page), assigned in JSON order: each page's `content` from first to last, and, on reaching a table, all its cells row by row and left to right before the next item.
AC: Given JanusSamples/c4.json, When processed, Then IDs run 1…N with no gaps, the page-1 IDs are 1…89, and every ID on page 2 is greater than every ID on page 1.

**FR-BOX-001 — Box positions**
Each box shall be the four corners the Structure output gives for that item (Structure FR-BOX-001). **Change from specReview:** nothing is derived — no adding up row heights, no grid-column model for `rowspan` cells — because every item and every cell now carries its own corners (Structure FR-TABLE-002). A merged cell is boxed over its whole merged extent.
AC: Given WorkedExample1, When processed, Then every cell box in the table's last row overlaps that row's text.
AC: Given SBC_Example_Data, When processed, Then the box for the header cell `"What You Will Pay"` spans both of the columns beneath it, and the box for a `rowspan` cell covers all of its rows.

**FR-BOX-002 — Barcode boxes**
A barcode's width is not in the JSON for linear codes, because the real length depends on the encoded data (and for a barcode drawn from text in a barcode font, cannot be determined at all). The document analyst sets the real size. The purpose of a barcode's box is only to put a numbered tag on the page that ties the barcode to its workbook row, so the analyst knows where to record its rules; the box's size is not a specification. **Change from specReview:** the skill shall draw the box from the barcode region in the extraction record (Structure FR-EXTRACT-001), i.e. the area the barcode occupies on this page, instead of searching the PDF for an unclaimed image. If no region is available, the skill boxes the known top, left, and height and says so (Rule 0); it never guesses a width.
AC: Given WorkedExample1, When processed, Then the barcode's box matches the barcode image `{575, 434, 602.5, 519}` pt within 2 pt.

**FR-BOX-003 — Split rows**
For a row marked `split: "start"`, the box shall have no bottom line; for `split: "end"`, no top line.
AC: Given PastDue_0001, When processed, Then the boxes for page 2's last row (`split: "start"`) have no bottom line, and those for page 3's first row (`split: "end"`) have no top line.

**FR-DRAW-001 — Drawing**
Boxes shall be red (#FF0000), unfilled, about 1 pt. Each label shall be white text on a solid red block at the box's top-left corner. A label may cover the content under it (the content is in the workbook).
AC: Given WorkedExample4, When processed, Then the annotated PDF has 14 boxes and 14 labels.

**FR-DRAW-002 — Label collisions**
No label shall cover another label. When a new label would overlap one already placed, it moves down below the earlier one. Only the label moves, never the box.
AC: Given WorkedExample5, When processed, Then the labels of the three rules at top 9.72in and of the caption paragraphs beneath them do not overlap one another.

**FR-ROW-001 — Workbook rows**
The workbook shall have exactly one row per ID, with the skill-filled columns in §5.1 completed and the analyst columns blank.
AC: Given any worked example, When processed, Then the set of IDs in the workbook equals the set of labels on the annotated PDF, and the Content of each paragraph row equals its `data` with runs concatenated.

**FR-MIXED-001 — Mixed text sizes**
**Change from specReview:** the workbook shall show `Yes` in the `Mixed text sizes` column for every item the Structure skill marked `mixed-heights: true` (Structure FR-MIXED-001), on digital and OCR pages alike, so that the analyst is reminded to investigate those requirements (e.g. superscript text). The column is otherwise blank. It is a reminder only; the skill does not say which words differ.
AC: Given the Structure output for c4.pdf, When processed, Then the rows with `Mixed text sizes == "Yes"` are exactly the items marked `mixed-heights: true`.
AC: Given WorkedExample4, When processed, Then no row has `Mixed text sizes == "Yes"`.

**FR-VER-001 — Tied to one PDF instance; versioned outputs**
Every output shall belong to the PDF instance recorded in the Structure JSON (Structure FR-PDFID-001, BR-006). The skill shall refuse a JSON whose `source.sha256` does not match the PDF. Outputs are versioned and never overwritten:
- the annotated PDF carries the Structure JSON version it was drawn from (`<name>_annotated.v<N>.pdf`) and records the PDF hash and N in its document metadata;
- the workbook is generated as revision 0 (`<name>_review.v<N>-0.xlsx`); when the analyst changes it, they save it as the next revision (`-1`, `-2`, …) with origin `analyst` on the `Version` sheet, leaving earlier revisions unchanged.
When the analyst corrects the Structure JSON (a new JSON version, Structure FR-VER-001), the skill is run again on that version and produces a new annotated PDF and a new revision-0 workbook for it. Moving the analyst's answers from the old workbook to the new one is a manual task this release (OOS-007).
AC: Given `c4.pdf` and `c4.v1.json`, When processed, Then `c4_annotated.v1.pdf` and `c4_review.v1-0.xlsx` exist, and the workbook's `Version` sheet records c4.pdf's SHA-256 and JSON version 1.
AC: Given `c4.v1.json` and a c4.pdf that has since changed, When processed, Then the skill writes nothing and reports the mismatch.
AC: Given `c4_review.v1-0.xlsx` already exists, When processed again on `c4.v1.json`, Then the existing file is not overwritten.

**FR-VER-002 — Comparable versions**
Any two workbooks (or annotated PDFs) for the same PDF instance shall be comparable, so the analyst can see what changed between them: the same columns in the same order, rows in ID order, and each row identifiable by Page and Location as well as by ID, since IDs can shift when the Structure JSON changes. `Content` is not a reliable key for matching, because the analyst edits it (§5.1). (The comparison tool itself is out of scope; OOS-007.)
AC: Given workbooks generated from `c4.v1.json` and `c4.v2.json`, When compared, Then every row can be matched by Page and Location where the item is unchanged, whatever its ID.

**FR-ORIG-001 — Original unchanged**
The skill shall not modify `<name>.pdf`, any Structure JSON version, or any earlier version of its own outputs.

# 7. Non-functional Requirements

**NFR-1 — Performance**
No requirements.

**NFR-2 — Scalability / Isolation**
No shared state between invocations.

**NFR-3 — Environment**
A Claude skill with a deterministic Python script (PyMuPDF and openpyxl; fallback: reportlab overlay merged with pypdf).

**NFR-4 — Determinism**
Given the same PDF and JSON version, the same IDs, boxes, and rows (the `Version` sheet's date excluded).

**NFR-5 — Language**
Inherits DocExtractor NFR-5.

**NFR-6 / NFR-7 — Security and Privacy**
The outputs contain the document's content and are written only beside the inputs. They carry the same sensitivity as the PDF, and protecting any PII in them is the end user's responsibility (Intent, Security).

**NFR-8 to NFR-12**
No stated requirements.

**NFR-13 — Usability**
Usable by an analyst with no knowledge of this project: plain column headings, a drop-down on `Conditional?`, free text where the analyst records mappings (`External Data?`, `Shared Content`, `Notes`), frozen header.

# 8. Business Rules

**BR-001 — The analyst decides**
The skill shall not fill the analyst columns and shall not suggest answers. (That is the future Dynamic Data skill.)

**BR-002 — Nothing unnumbered**
Every leaf item gets an ID and a box. The analyst can mark an item as irrelevant but cannot see a missing one.

**BR-003 — Never guess** (Rule 0)
Positions and content come from the JSON (and, for barcode extent, DocExtractor). Anything that cannot be determined is reported, not estimated.

**BR-004 — Fix the source, not the drawing**
When a box lands in the wrong place, the fix belongs in the Structure output's corners (Structure FR-TABLE-002), not in adjustments here. The drift specReview saw with cumulative row heights cannot happen now that each cell carries its own corners.

**BR-005 — One way only**
The path always runs one way: document → annotated PDF and initial workbook. The skill never reads back a workbook or an annotated PDF, never merges an analyst's work into a new run, and never regenerates a document from them. What it produces is a starting point and a checklist that tells the analyst what has to be worked out; everything after that belongs to the analyst (OOS-004, OOS-009, OOS-010).

# 9. Non-Goals / Out of Scope

**OOS-001** — Identifying variable data or suggesting data sources (future Dynamic Data project).
**OOS-002** — Finding or recording exactly how to obtain each item's data (system, table, query). The skill provides the place to record it; a person fills it in afterwards (§0, OQ-2).
**OOS-003** — Connecting to or validating against any data source.
**OOS-004** — Reading back a completed workbook.
**OOS-005** — Running the Structure skill (IF-001).
**OOS-006** — Editing boxes interactively.
**OOS-007** — A tool that compares versions, or that carries analyst answers from one workbook to another (between JSON versions, or to a new PDF instance). Future tool; this release only keeps versions and makes them comparable (FR-VER-002).
**OOS-008** — Capturing generation requirements (Structure OOS-010), such as keeping a row group together or the continuation header a split group needs. They cannot be read from the document and are the analyst's to supply; the workbook's free-text `Notes` column is the only place it offers for them.
**OOS-009** — Turning the annotated PDF and the workbook into a report. Once completed they hold what the document is and where its data comes from, and that eventually has to become a readable account of what the software is supposed to do, so that nobody has to read the code to find out. Producing that report is not this skill's job.
**OOS-010** — Keeping the artifacts current as documents and data paths change. The analyst updates them; when the changes are large enough that the artifacts are superseded, a new tool will be needed to carry across what still applies and to identify what has to be gathered afresh (OOS-007).

# 10. Limits / Constraints

**LIM-001 — No exfiltration**
Inherits DocExtractor LIM-001, subject to Structure OQ-12.

**LIM-002 — Always third in the process**
The process is always extraction (DocExtractor), then structure (Structure skill), then mapping (this skill). The Mapping skill never runs alone or directly on DocExtractor output. Item boundaries and positions are the Structure skill's; this skill does not regroup or re-measure content (except barcode extent, FR-BOX-002).

# 11. Product Success Metrics

**SCS-001** — All acceptance criteria in §6 pass.
**SCS-002** — For WorkedExample1 and WorkedExample5 (specReview's tested documents), every box lands on its item with no manual correction.
**SCS-004** — For SBC_Example_Data, the output matches the reference outputs: the same 271 IDs in the same order, the same `Content` for each (before the analyst's edits), and boxes in the same places as `SBC_Example_Data_annotated.pdf`.
**SCS-003** — A multi-page document (c4) is numbered and boxed correctly (untested in specReview).

# 12. Deferred Decisions (design)

**DD-1** — Label size and font.
**DD-2** — Column widths in the workbook.
**DD-3** — File-naming details for versions (e.g. zero-padding) and which PDF metadata fields hold the hash and version.

# 13. Open Questions

- **OQ-1** — *Resolved v0.2:* granularity is every leaf item, including each table cell and each rule (FR-ITEM-001).
- **OQ-2** — *Resolved v0.3:* the skill only creates the place to record information; neither it nor the Structure skill can supply the data. A person completes the workbook afterwards, working with a DBA, database tools, and data catalogs. Automating that work is the future Dynamic Data project. The workbook keeps specReview's columns.
- **OQ-3** — *Resolved v0.2:* PDF and .xlsx (IF-002).
- **OQ-4** — *Resolved v0.2:* written beside the inputs. *Amended v0.3:* names are versioned, `<name>_annotated.v<N>.pdf` and `<name>_review.v<N>-<M>.xlsx` (FR-VER-001).
- **OQ-5** — *Resolved v0.3:* IDs are positions and are not stable across versions. Outputs are tied to one PDF instance (a changed PDF means new outputs, and the analyst moves answers across by hand). Within one PDF instance, every Structure run, analyst correction, and workbook revision is a new, numbered version; versions are kept and comparable (FR-VER-001, FR-VER-002). Comparison and carry-forward tools are future work (OOS-007).
- **OQ-6** — *Resolved v0.2:* no interactive editing (OOS-006).
- **OQ-7** — *Resolved v0.3:* no. The process is always extraction, structure, mapping (LIM-002).
- **OQ-8** — *Resolved v0.2:* invisible text is a paragraph in the Structure output, so it is numbered like any other paragraph.
- **OQ-9** — *Resolved v0.3:* the Structure skill reports form controls as `form_control` items with bounding boxes (Structure FR-FORM-001); this skill numbers and boxes them, and the Content column marks them as controls so the analyst knows to write code rules for them.
- **OQ-10** — *Resolved v0.3:* no. Confidence values are for applications that want the extracted values; the Mapping skill and its workbook do not use them.
- **OQ-11** — *Resolved v0.3:* WorkedExample1.json (71 leaf items) is newer than specReview's notes (69). 71 is correct; the note in specReview's SKILL.md is stale.
- **OQ-12** — *Resolved v0.3:* the skill is named Mapping. All of these components are part of a new set of tools, so names may still change.
- **OQ-13** — *Resolved v0.3:* the Structure output uses generic `name`s (Structure OQ-15), so the Content column shows `[Image: IMAGE001]` etc. The existing c4.json (`ref`) is a reference for the Structure skill, not an input to this skill; the leaf count for page 6 will change once its image becomes text (Structure FR-OCRBG-001).
- **OQ-14** — *Resolved v0.3:* yes; mixed sizes are always flagged, on digital pages as well as OCR pages (Structure FR-MIXED-001).
- **OQ-15** — *Resolved v0.3:* option (a). The Structure skill retains each page's raw DocExtractor output with its JSON (Structure FR-EXTRACT-001), and this skill reads barcode regions from it. The barcode box is a locator tag, not a size (FR-BOX-002).
- **OQ-16** — *Resolved v0.5:* `Content` starts as the extracted text and is the analyst's working column thereafter, moving toward what an author would implement. Comparisons match rows by Page and Location, not by content (FR-VER-002).
- **OQ-17** — *Resolved v0.5:* tokens are the analyst's. `DI00001` and `SC00001` are mapping points between an XPath in the data model and a single symbol in the author's content; the skill neither assigns nor interprets them.
