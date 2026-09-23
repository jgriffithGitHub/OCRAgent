---
# Product Requirements Specification — Validation Test Set
**Status:** Draft v0.1 — 2026-09-22 (first draft; the specimen list and the equivalence rules are proposals, open questions in §8)
---

# Related Documents
**Intent:** [intent/Intent.md](intent/Intent.md) · **Tool:** [DocExtractor_PRS.md](DocExtractor_PRS.md) · **Skills:** [Structure_PRS.md](Structure_PRS.md), [Mapping_PRS.md](Mapping_PRS.md)

# 0. Context

The existing corpus is a collection of documents that happened to be available. It leaves known gaps (Structure OQ-9), and its expected outputs were produced by hand or by the skills being replaced, so several were found to be stale or wrong during specification.

This test set is built the other way round: **each specimen is authored to prove something, and the same specimen is produced by four independent platforms.** If the pipeline describes the document rather than the habits of whatever produced the PDF, all four must yield the same description within tolerance. Where they do not, the difference is either a defect or a fact about PDFs worth writing into a spec.

It also gives expected output that nobody measured by hand. Authoring the specimen means the structure is known before the PDF exists.

# 1. The four implementations

| ID | Platform | Produced by | Notes |
|---|---|---|---|
| **A** | XSL-FO rendered by Apache FOP 2.11 | Jeff authors the FO | Also renders the same FO to **AFP** and to **Area Tree XML** (`-at`), which gives exact per-page geometry (§3) |
| **B** | Script-built PDF (ReportLab or equivalent, run locally) | Claude | Draws text and shapes directly; no layout engine, so positions are whatever the script states |
| **C** | Programmatic PDF with **iText** | an application to be written | Closest to hand-built output; the only one of the four that can also produce AcroForm controls |
| **D** | **JasperReports** (JRXML → PDF) | to be built | Band-based; a table that breaks across pages is its native idiom |

Each platform draws the same page differently — different text-run splitting, different use of rectangles versus lines for rules, different font embedding and subsetting. That variation is the point: it is what the equivalence rules in §5 are written against.

**None of these are part of the product.** They produce test material; nothing here is built into DocExtractor or the skills.

# 2. Specimens

Each specimen is one document, authored four ways, with an intent sheet (§3). Sizes are letter portrait unless stated.

**S1 — Table continuing across pages**
A table of many rows, long enough to run over three pages, with a header row repeated on each continuation and at least one row whose text is tall enough to split across the page break.
Proves: Structure FR-TABLE-004 (`split: "start"` / `"end"`), FR-TABLE-001 (one table per page, header repeated as a row), Mapping FR-BOX-003 (no line at a split edge), Mapping FR-NUM-001 across pages.
Closes: the only requirement with no test today.

**S2 — Merged cells**
A two-row header where one cell spans two columns and three cells span both rows, over a body whose first column spans several rows and whose last column spans three.
Proves: Structure FR-TABLE-001 (`rowspan`, `colspan`, corners over the merged extent), FR-TABLE-002 (cell corners), Mapping FR-BOX-001 (a merged cell boxed over its whole extent).
Note: SBC covers this in a real document, but its reference JSON predates the current spec.

**S3 — Text the page does not show plainly**
On one page: a superscript and a subscript; text drawn stroke-then-fill to simulate bold; a line of 1 pt text in the background color (a printer mark); white text on a dark filled shape; a block rotated 90°.
Proves: Structure FR-TEXT-001 (duplicate text reported once, bold), FR-HIDDEN-001, FR-MIXED-001 (smaller **and** raised or lowered), FR-ROTATE-001; DocExtractor FR-TEXT-003/004.
Caution: stroke+fill duplication and invisible text may not be expressible on every platform (§8).

**S4 — AFP, and its digital twin**
The same page produced twice from implementation A: once to PDF (digital text) and once to AFP, converted to PDF by the same route as c4.pdf. The page carries a band of colored background with text over it, small print, and a printer mark.
Proves: DocExtractor FR-OCR-001/002 and the DD-7 reporting floor; Structure FR-OCRBG-001 (text on a background whose color is `"see original document"`), FR-OCRHEIGHT-001 (`text-height` in points), FR-STYLE-001 on OCR pages.
Why it matters: the digital twin is the ground truth for the OCR run. Today c4 is the only AFP case and its expected output was never reviewed a second time; here the correct answer is known from the same source document.

**S5 — Everyday layout**
Bulleted and checkbox-glyph list items with wrapped continuation lines; a fill-in line made of underscores with a caption beneath; a drawn rule with a caption beneath; a shaded single-cell box; a page background color; two images, one of them a barcode.
Proves: Structure FR-LIST-001, FR-TABLE-005 vs FR-RULE-001 (the DD-10 distinction), FR-TABLE-003, FR-BG-001, FR-IMAGE-001, FR-BARCODE-001.

**S6 — Volume**
The S1 table at scale: 500 pages, and one run at 5,000 pages.
Proves: Mapping numbering with no gaps at volume; Structure determinism (NFR-4) and versioning behavior; DocExtractor per-page isolation (NFR-2). Also the first honest measurement of how long the process takes per page.

**S7 — Form controls (implementation C only, optional)**
A page of AcroForm controls: empty text boxes, checkboxes, radio group, choice list, and a printed box drawn beneath one control.
Proves: Structure FR-FORM-001 (four corners, type, name, value; the printed frame accounted for as the control's), Mapping Content showing `[Form control: …] name = value`.
Only iText can produce this; fw9 already covers it in a real document, so this specimen is optional.

# 3. Ground truth for each specimen

Every specimen carries two things beside the four PDFs:

1. **An intent sheet** (`<specimen>/intent.md`): what the specimen contains, written before it is produced — the items, their nominal positions and sizes, the structure intent (this is one table; this cell spans three rows; this row is expected to split on page 2), and which requirements it proves.
2. **The FOP Area Tree XML** for implementation A: exact geometry per page, produced by the engine rather than measured by hand. Units and origin must be converted to this project's inches-from-top-left (§8).

Together these replace hand-measurement: the intent sheet says what the structure is, the area tree says where it landed.

# 4. Layout on disk (proposed)

```
testCases/testset/<specimen-id>/
    intent.md
    A-fop/         source.fo  out.pdf  out.afp  afp-converted.pdf  areatree.xml
    B-script/      build.py   out.pdf
    C-itext/       <source>   out.pdf
    D-jasper/      report.jrxml  out.pdf
    expected/      <specimen>.v1.json          # Structure output, once agreed
```

# 5. What the four implementations must agree on

Given the four PDFs of one specimen, the Structure output shall be the same in:

- the set of content items and their types, and their order;
- every location and size, within ±0.02 in of the intent sheet;
- table shape: row count, cell count per row, `rowspan` / `colspan`, and which rows are split;
- list markers (code point) and marker spacing;
- text content, word for word.

**Differences that are expected and allowed:**

- **Font names.** Each platform embeds and names fonts its own way, including subset prefixes. Style strings will differ (Structure FR-STYLE-001 reports what the PDF declares).
- **How a rule is drawn.** A thin filled rectangle in one platform, a stroked line in another. Both are a `rule`.
- **Word splitting.** Kerning and text-run boundaries differ, so DocExtractor may report different word counts for the same sentence (its DD-5). The Structure output must still produce the same paragraph text.
- **Cell background extent.** The painted area behind a cell may differ by a fraction of a point between platforms.
- **Image encoding and resolution.**

Anything else that differs is a finding: either a defect in the skill, or a rule the spec has not yet stated.

# 6. Requirements this test set must satisfy

**TS-001** — Every specimen has an intent sheet written before the document is produced.
**TS-002** — Every specimen exists in at least implementations A and one other; S4 requires A; S7 requires C.
**TS-003** — All content is synthetic: no customer data, no third-party logos or marks, no fonts that cannot be redistributed.
**TS-004** — Each implementation is reproducible from its source (the FO, the script, the iText application, the JRXML), which is kept with the output.
**TS-005** — The expected Structure output for each specimen is agreed once, from the intent sheet and the area tree, and then versioned like any other output (Structure FR-VER-001).
**TS-006** — Where the four implementations disagree, the disagreement is recorded with the specimen, and resolved either as a defect or as a new rule in the relevant PRS.

# 7. What this test set does not do

- It does not replace the real documents in `testCases/`. A corpus of only generated fixtures specifies the generators, not documents in the wild.
- It does not test generation requirements (Structure OOS-010). A specimen can show that a group broke across a page; it cannot show that a rule said it should not.
- It does not measure OCR accuracy as a percentage; S4 tests behavior — what is reported, at what confidence, and what is marked unresolved.

# 8. Open questions

- **OQ-1** — Which converter turned AFP into PDF for c4.pdf? S4 must use the same one, or the OCR case will not resemble the documents this project exists for.
- **OQ-2** — Which font is available to all four platforms, embeddable and redistributable? A common family (e.g. a DejaVu or Liberation face) keeps the comparison honest; otherwise each implementation's text will differ in size and wrapping.
- **OQ-3** — Can S3's effects be produced on all four platforms — stroke+fill duplicate text, invisible 1 pt text, rotation? If not, which platform is authoritative for that specimen, and do the others simply omit the effect?
- **OQ-4** — Barcodes in S5: FOP needs an extension, JasperReports has a barcode component, iText has its own. Are these close enough to compare, or should the barcode be a placed image in every implementation?
- **OQ-5** — The FOP area tree is an internal format "for testing and verification", not a contract. What conversion is needed to compare it with this project's coordinates, and is it stable enough between FOP versions to keep as expected output?
- **OQ-6** — Does S6 run at 5,000 pages as one document, or as a 5,000-page document split into pages by the caller? DocExtractor sees one page at a time either way, but the splitting cost is real and currently unmeasured.
- **OQ-7** — Who builds implementations C and D, and when? The set is useful with A and B alone; C and D add the platform independence that is the point of the exercise.
