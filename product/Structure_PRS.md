---
# Product Requirements Specification — Structure Skill
**Status:** Draft v0.4 — 2026-09-22 (v0.4: every item and cell is located by its four corners instead of top-left plus width/height (FR-BOX-001, OQ-22); `colspan` kept; one table per page rather than one per rowspan group; cell backgrounds reported. v0.3: `documentName` dropped (OQ-3); expected output for c4.pdf found (`testCases/JanusSamples/c4.json`) and c4 acceptance criteria added; OQ-6 resolved from it; OQ-15 resolved (generic image names, four edges); OQ-16 resolved (text in raster areas of an OCR page is reported as text on a colored background, FR-OCRBG-001), and OQ-17 resolved: the color behind rasterized text is reported as unknown (Rule 0); DD-7 decided: unknown values are written as `"see original document"` with no qualifier (BR-005); OCR text items report their measured `text-height` (line height from the tallest word in each line) and a `mixed-heights` flag instead of a font size (FR-OCRHEIGHT-001; DD-8 decided, tolerance 0.5 pt); `mixed-heights` also applies to digital pages (FR-MIXED-001); raw DocExtractor output retained with each version (FR-EXTRACT-001); confidence stays in that record, not the JSON (OQ-5, Persona 3 removed); style strings carry the PDF's own font name and size, and no derived layout properties (FR-STYLE-001, OQ-4, OQ-21 resolved); fill-in lines with captions are tables (FR-TABLE-005, OQ-10); form controls carry their value (FR-FORM-001, OQ-20); SBC_Example_Data.pdf (merged cells) and PastDue_0001.pdf (split rows) added with their reference JSONs, closing OQ-9b; their format deviations raised as OQ-22; duplicate stroke+fill text is reported once, bold (FR-TEXT-001, OQ-14); unrecognized content is reported in place (FR-DIAG-001, OQ-13); OQ-11 and OQ-12 resolved; `form_control` content item added (FR-FORM-001); annotations excluded (OQ-7 resolved, OOS-009); results tied to one PDF instance and every output versioned (FR-PDFID-001, FR-VER-001/002, BR-006); OQ-18 resolved: `text-height` is in points to 0.5 pt; OQ-19 resolved: on OCR pages a word counts as a different size only if it is both smaller and raised or lowered (best effort). v0.2: re-based on DocSpec `skills/specScan/SKILL.md`, the skill being replaced; OQ-1, OQ-2, OQ-8 resolved; hidden content follows specScan; tables, rotation, barcodes, split rows specified. v0.1: first draft from DocExtractor_PRS.md v0.8 and WorkedExample1–5.json)
---

# Related Intent Document
**Intent Document:** [intent/Intent.md](intent/Intent.md)

# 0. Context

The Structure skill is the second of the three components in this project:

1. **DocExtractor** (tool, [DocExtractor_PRS.md](DocExtractor_PRS.md)) — reports what a single PDF page *contains*.
2. **Structure skill (this spec)** — derives the layout: margins, page background, paragraphs, list items, tables, rules, images, barcodes. Produces the `specScan` JSON.
3. **Mapping skill** ([Mapping_PRS.md](Mapping_PRS.md)) — numbers every leaf item and produces an annotated PDF and a review workbook.

Identifying which content is variable data (the **Dynamic Data** skill) is a separate, future project (OOS-001).

**Origin.** This skill replaces the existing DocSpec skill `specScan` (`C:\Projects\DocSpec\skills\specScan\SKILL.md`). specScan does two jobs: it *measures* the page (a "sliding reveal", or pdfplumber/pdftoppm) and it *interprets* what it measured. Watching Claude run specScan showed that the measuring can be done by a tool; that tool is DocExtractor. The Structure skill is specScan with the measuring removed: it keeps specScan's output format and interpretation rules, and takes all of its facts from DocExtractor.

**Authority.** specScan's SKILL.md ("Report Format" and "Process" sections) and its WorkedExample1–5.json define the output this skill must reproduce. Where this spec and specScan differ, the difference is stated as a change (marked **Change from specScan**) or an open question.

# 1. Purpose & Scope

The Structure skill receives a PDF, obtains DocExtractor output for each page, and writes one `specScan` JSON file describing every page: margins, page background, and the content items needed to reproduce the page (paragraphs, list items, tables, rules, images, barcodes), with exact positions.

In scope: grouping primitives into content items and describing their location, size, and style. Out of scope: the business meaning of any item, and which content is variable data (§9).

# 2. Glossary / Ubiquitous Language

Terms defined in DocExtractor_PRS.md §2 have the same meaning here. **Field** remains reserved for the future Dynamic Data skill.

- **document**: the whole input PDF (all pages). DocExtractor sees one page; this skill sees the document.
- **content item**: one entry in a page's `content` list: `paragraph`, `listitem`, `table`, `rule`, `image`, `barcode`, `form_control`, or `unrecognized`.
- **form control**: an interactive form widget declared in the PDF (DocExtractor §2). It is not text: the analyst has to know an item is a control in order to write the code rules for it.
- **leaf item**: a content item that holds content: every content item except `table`, plus every table cell. A table is a container. Every leaf item carries enough information to draw a box around it without guessing (FR-BOX-001).
- **paragraph**: a block of text, possibly several wrapped lines, located by its four corners, covering every wrapped line.
- **run**: a span of text with one style inside a paragraph, list item, or cell (`{text, style}`). Used only when the style changes within the block.
- **list item**: any line introduced by a marker glyph: bullet, number, or checkbox character. A checkbox's state is expressed by which glyph is the marker.
- **marker space**: the gap between the marker and the start of the item's text.
- **table**: content in rows and cells. Each row has `props` (`split`) and `columns` (cells); every cell carries its own corners, so a row's extent is derivable. A cell may carry `rowspan` or `colspan`.
- **split row**: a table row that starts on one page and resumes on the next (`split: "start"` / `"end"`; otherwise `"no"`).
- **rule**: a thin line or filled bar used as a divider or underline, reported with all four edges.
- **page background**: a fill color behind everything on the page. Omitted when white.
- **native orientation**: how a rotated item looks before rotation (a barcode read left to right).
- **style string**: the font as the PDF declares it, name and size, e.g. `"AvenirNextLTCom-Demi 16pt"` (FR-STYLE-001).
- **PDF instance**: one specific PDF file, identified by the SHA-256 hash of its bytes. A PDF with any change is a different instance, even under the same name.
- **version**: one saved state of an output for a given PDF instance, numbered 1, 2, 3, … A new version is created each time the skill runs or the analyst corrects the output; earlier versions are kept.
- **extraction record**: the DocExtractor output for each page, saved exactly as DocExtractor returned it, beside the Structure JSON it was used to produce (FR-EXTRACT-001).
- **reading order**: the order in which a cover sheet slid down the page would expose each item's top-left corner (specScan's "sliding reveal").
- **Rule 0**: specScan's rule: never guess; if something cannot be recognized or described, say so, with its location.
- **"see original document"**: the value written in place of anything the skill could not see or could not resolve (BR-005). It tells the document analyst to check the original PDF at that item.
- **line height**: on an OCR page, the height of one line of text, set by the tallest word in the line (DocExtractor reports word boxes, not character boxes, so the tallest word stands in for the tallest character).
- **text height**: the measured height of the text in an item: its tallest line height. A measurement of the rendered text, not a font size (FR-OCRHEIGHT-001).
- **mixed heights**: an item whose words differ in height within a line, or whose lines differ in height, e.g. superscript text or a larger first word.

# 3. Users

## Persona 1: Document analyst (primary)
- Role: a person who reverse-engineers an existing document so that it can be rebuilt in a document-generation system.
- Problem statement: needs a complete layout specification, independent of any document-generation system, so that each page can be reproduced without measuring it by hand.

## Persona 2: Mapping skill
- Role: the skill that numbers leaf items and produces the review artifacts (Mapping_PRS.md).
- Problem statement: needs a JSON file whose name matches the PDF, with a bounding box for every leaf item, accurate enough that boxes computed from it (including cumulative table-cell positions) land on the right content.

Not a persona: a **Consuming Application** that wants extracted values and their confidence does not use this skill's JSON. It reads the extraction record saved beside it (FR-EXTRACT-001), which is DocExtractor's own output with every value, confidence score, count at threshold, and extraction method (DocExtractor Persona 2).

# 4. User Stories

**US-001**: As a document analyst, I want every paragraph, list item, table, rule, image, and barcode on each page with its location, size, and style, so that I can rebuild the document.

**US-002**: As a document analyst, I want tables returned as rows of cells with their corners, spans, borders, and backgrounds, and rows that split across pages marked, so that I can rebuild them as tables.

**US-003**: As a document analyst, I want printer marks and other invisible text reported as ordinary paragraphs with their true color and size, so that I know they exist even though I cannot see them.

**US-004**: As the Mapping skill, I want every leaf item to have an accurate bounding box, so that I can draw a numbered box on it.

**US-005**: As a document analyst, I want anything the skill could not recognize reported with its location, so that I can deal with it rather than trust a guess.

# 5. External Interface

**IF-001 — Invocation**
The skill is invoked by an agent (or by a person through an agent) with a PDF file. It writes `<name>.v<N>.json` beside the PDF, where `<name>` is the PDF's file name without extension and equals the JSON's `fileName` (specScan step 1; the Mapping skill depends on the matching names), and `<N>` is the next unused version number for that PDF (FR-VER-001). **Change from specScan:** specScan wrote `<name>.json` and overwrote it on each run. An optional threshold is passed through to DocExtractor.

**IF-002 — Pages**
The skill processes every page. DocExtractor extracts only the first page of what it is given (DocExtractor FR-PAGE-002, LIM-002), so the skill gives DocExtractor one page at a time. This makes the Structure skill the "Consuming Application" that DocExtractor's IF-001 rationale refers to.

**IF-003 — Source of facts**
Every location, size, style, color, and text value in the output comes from DocExtractor output. **Change from specScan:** the skill does not measure the PDF itself (no sliding reveal, no pdfplumber). Splitting the PDF into pages is not measuring.

**IF-004 — Unrecognized content**
Content the skill cannot recognize or describe is reported in the skill's response to its caller, with its location, per Rule 0 (e.g. "I could not recognize the content located at top=4in, left=0.75in, right=7.5in, bottom=6in"). It is also recorded in the JSON: as a `paragraph` when a value was extracted but could not be classified, or as an `unrecognized` item when there is a location but no value (FR-DIAG-001).

## 5.1 Output (as defined by specScan SKILL.md "Report Format")

All measurements are strings in inches to 0.01 in (e.g. `"0.52in"`), relative to the top-left corner of the page. The one exception is `text-height`, which is in points to 0.5 pt (e.g. `"8.5pt"`), the unit authors use for type sizes in styles. Colors are `#RRGGBB`.

```
{
  "fileName": <string>,                    // matches the PDF's name
  "source": { "file": <string>, "sha256": <string> },   // the PDF instance (FR-PDFID-001)
  "extraction": [ <string>, ... ],       // file names of the extraction record, one per page (FR-EXTRACT-001)
  "version": { "number": <int>, "based_on": <int|null>, "origin": "structure-skill" | "analyst", "created": <ISO 8601 timestamp> },   // FR-VER-001
  "pages": [
    {
      "margins": { "top", "bottom", "left", "right" },
      "background": <color>,               // omitted when the page is white
      "content": [ <content item>, ... ]   // in reading order
    }
  ]
}
```

Content items (all non-barcode items are located by their top-left corner):

- **paragraph**: `data` (string, or list of runs), `style`, `location {top, left, bottom, right}` (the whole block, all wrapped lines); `color` when not black.
- **listitem**: `location {top, left, bottom, right}` (from the top-left of the marker through the end of the content), `marker` (code point, e.g. `"0x2022"`), `marker-style`, `marker-space`, `item-content` (string or list of runs), `style`.
- **table**: `location {top, left, bottom, right}`; `border` (e.g. `"1pt solid #000000"`) only when the outer edge is drawn; `rows[]`: `props {split}` and `columns[]` of cells. A cell is `{type: "text", data, style, borders, background, location {top, left, bottom, right}}` or `{type: "listitem", marker…, item-content, …}`, optionally with `rowspan` / `colspan`. A merged cell's corners cover its whole merged extent. An empty cell has `data: ""`.
- **rule**: `location {top, left, right, bottom}`, `color`.
- **image**: `name` (unique, e.g. `IMAGE001`), `location {top, left, bottom, right}`.

**Change from specScan — four corners.** Every content item and every cell is located by `{top, left, bottom, right}`. specScan reported a top-left corner plus `width` and `height` (and a row `height` that cells inherited), which suited a process where measuring and interpreting happened in one step. With extraction split out, and OCR in the mix, each item's extent comes straight from DocExtractor's boxes, so reporting the corners is both simpler and more reliable: the Mapping skill reads a box instead of adding up row heights (its FR-BOX-001), and a small error in one row can no longer push later boxes off the page. `width` and `height` are derivable and are not reported. The worked examples use the old form; comparisons convert (`right = left + width`, `bottom = top + height`).

**Change from specScan:** there is no `documentName`. specScan step 2 asked for a human-readable name describing the document; neither DocExtractor nor this skill has the information needed to set it, and choosing one would mean inferring the document type (BR-001). The existing worked examples still contain `documentName`; it is ignored when comparing output to them (SCS-002).
- **barcode**: `location {top, left, height, rotation}`, plus `width` for QR and other 2-D codes only.
- **unrecognized**: `location {top, left, bottom, right}` and nothing else: DocExtractor located something but extracted no value from it (FR-DIAG-001). Added by this spec; not in specScan.
- **form_control**: `location {top, left, bottom, right}`, `control_type` (`text` | `checkbox` | `radio` | `choice` | `signature` | `button`), `name` and `value` (as declared). Added by this spec (FR-FORM-001); not in specScan.

Addition to the specScan format (decided): on OCR pages, text-bearing items (paragraphs, list items, table cells) carry `text-height`, and `mixed-heights: true` when their text has mixed heights (FR-OCRHEIGHT-001).

Not added: confidence information, which remains in the extraction record (OQ-5); annotations, which are not part of the document being described (OOS-009).

## 5.2 Test corpus

The documents below are what happened to be available. A purpose-built set, each specimen produced by four platforms, is specified in [TestSet_PRS.md](TestSet_PRS.md); it is where the gaps in OQ-9 are meant to be closed.

| File | Pages | What it exercises |
|---|---|---|
| WorkedExample1.pdf / .json | 1 | Letter; logo image; rotated (90°) raster barcode; one 9-row label/value table (rows measure 0.15in for the header and about 0.21in each after it); 2 rules. JSON styles stale (DocExtractor OQ-9) |
| WorkedExample2.pdf / .json | 1 | Fill-in-the-blank letter (`"I, ______, of ______,"`) represented as 5 tables; 1 rule |
| WorkedExample3.pdf / .json | 1 | Statement with grey page background (#E4E4E4); 9-column transaction table; 5 full-width rules |
| WorkedExample4.pdf / .json | 1 | Checkbox-glyph (☐, MS Gothic) and bullet (Symbol) list items; styled runs inside list items; no paths |
| WorkedExample5.pdf / .json | 1 | 2 images (logo, scanned signature); 3 signature rules; a bordered table whose cells are Wingdings checkbox list items; paragraphs with styled runs |
| TestCase4.pdf | 2 | Rotated text; stroke+fill duplicate text; white text on a dark shape; raster title (not OCR'd) |
| JanusSamples/c4.pdf / c4.json | 6 | AFP-to-PDF (OCR); printer marks above the top margin; 8 tables including a 41-row fund-activity table, grey (#CECFD1) cell shading, a bordered disclaimer box; page 6 is a single image. The JSON has not had a second review pass and differs from the specScan format in places (OQ-15, OQ-16) |
| SBC_Example_Data.pdf (.json for reference only) | 8 | Landscape (11 × 8.5 in) Summary of Benefits and Coverage. The benefits chart on pages 2–4 has a two-row header with a `colspan` ("What You Will Pay" over two columns) and `rowspan` header cells, body cells spanning several rows in both the first and last columns, and colored cell backgrounds. Its JSON predates this spec: one table per group, no `colspan`, numeric lengths, and descriptive image names (`IMAGE001_LOGO`) where this spec uses generic ones (OQ-15), so it is not the expected output (OQ-22). Its images do use four corners |
| PastDue_0001.pdf / .json | 4 | Past-due notice. A 3-column table of products continuing across pages 2, 3, and 4, with two rows split across a page boundary (`split: "start"` / `"end"`); page 1 has a logo image and a barcode |
| fw9.pdf, fw9_filled.pdf, fw9_filled_flattened.pdf | 6 | DocExtractor fixtures: empty fillable form (23 controls on page 1: 15 text, 8 checkbox); the same form filled; the filled form flattened (no controls) |
| barcodes.pdf | 1 | DocExtractor fixture: vector Code 39, vector QR, barcode-font text, decoy stripes |
| TestCase1.pdf, TestCase5.pdf | 1, ? | Present in specScan's folder; no stated purpose (OQ-9) |

# 6. Functional Requirements

Positional tolerance: ±0.02 in unless stated. Style values are not checked against WorkedExample1.json (stale).

**FR-DOC-001 — Document**
The skill shall write one JSON file for the whole document, with one `pages` entry per page in page order, and `fileName` equal to the PDF's name without extension.
AC: Given c4.pdf with no earlier outputs, When processed, Then `c4.v1.json` is written beside it with `fileName == "c4"` and 6 pages.
AC: Given TestCase4.pdf, When processed, Then `pages` has 2 entries and `"RECIPE"` appears in page 2's content and not page 1's.

**FR-PDFID-001 — Tied to one PDF instance**
The output shall record the PDF instance it describes: the PDF's file name and the SHA-256 hash of its bytes (`source`). An output describes that instance only. If the PDF changes in any way, its outputs no longer apply; a new set of outputs is produced for the new instance, starting again at version 1 (BR-006).
AC: Given c4.pdf, When processed, Then `source.sha256` equals the SHA-256 of c4.pdf's bytes.
AC: Given a copy of c4.pdf with one byte changed and saved under the same name, When processed, Then its `source.sha256` differs from the original's.

**FR-EXTRACT-001 — Retain the raw extraction**
The skill shall save each page's DocExtractor output, unmodified, beside the Structure JSON (e.g. `<name>.v<N>.p<K>.extract.json` for page K; naming: DD-9), and list those files in the JSON's `extraction` field. A version created by the analyst reuses the extraction record of the version it is based on rather than creating a new one. The extraction record is the evidence behind every Structure decision: it lets the analyst check a grouping, a Rule 0 report, or an OCR reading against what DocExtractor actually found, and it supplies facts the specScan format does not carry (e.g. a barcode's drawn extent, used by the Mapping skill). It matters most on OCR pages, where the recognized words, their confidences, and their boxes exist nowhere else.
AC: Given c4.pdf, When processed, Then `c4.v1.json` lists 6 extraction files, each exists beside it, and each is byte-identical to DocExtractor's output for that page.
AC: Given an analyst correction saved as `c4.v2.json` with `based_on == 1`, When inspected, Then its `extraction` field names the version-1 extraction files.

**FR-VER-001 — Versions**
Each run of the skill shall write a new version (`<name>.v<N>.json`, N = the next unused number) and shall never overwrite or modify an existing version. Each version records its number, the version it was based on (`based_on`; null for version 1 or a fresh run), its origin (`structure-skill`, or `analyst` for a correction made by the document analyst), and when it was created. An analyst who corrects an output saves the result as the next version with origin `analyst`; the earlier version remains unchanged. A new version for a *different* PDF instance is not permitted: if the highest existing version records a different `source.sha256`, the skill stops and says so (BR-006).
AC: Given c4.pdf processed twice, When the second run completes, Then `c4.v1.json` is unchanged and `c4.v2.json` exists with `version.number == 2`.
AC: Given `c4.v1.json` and a modified c4.pdf under the same name, When processed, Then the skill writes nothing and reports that the PDF no longer matches its outputs.

**FR-VER-002 — Comparable versions**
Any two versions for the same PDF instance shall be comparable item by item, so that the analyst or author can see what changed between them (e.g. a grouping decision that changed on a re-run, or an analyst's correction). To make this possible, every version shall be written in the same canonical form: the same key order, the same indentation and line breaks, content items in reading order, and one item per block of lines, so that an ordinary line-by-line comparison shows only real differences. Each leaf item is identifiable across versions by page, type, and location, not by its position in the list. (A tool that performs the comparison is out of scope for this release; OOS-007.)
AC: Given c4.pdf processed twice with no change in grouping, When `c4.v1.json` and `c4.v2.json` are compared line by line, Then they differ only in the `version` block.

**FR-MARGIN-001 — Margins**
The skill shall report each page's margins.
AC: Given WorkedExample4.pdf, When processed, Then margins are top 0.52in, bottom 0.90in, left 0.90in, right 0.90in.
AC: Given WorkedExample3.pdf, When processed, Then margins are top 0.32in, bottom 0.20in, left 0.14in, right 0.14in.
AC: Given c4.pdf, When processed, Then every page's margins are top 0.25in, bottom 0.31in, left 0.63in, right 0.65in.
Printer marks do not count toward margins: on c4.pdf, `"JAN005237179"` (top 0.11in) and `"Confirm - Mail 1"` (top 0.07in) lie above the 0.25in top margin (OQ-6).

**FR-BG-001 — Page background**
When the page has a fill color behind everything, the skill shall report it as `background` and not as a content item. A white page has no `background` key.
AC: Given WorkedExample3.pdf, When processed, Then `background == "#E4E4E4"`.
AC: Given WorkedExample4.pdf, When processed, Then no `background` key is present.

**FR-PARA-001 — Paragraphs**
The skill shall report each block of text as one paragraph (not one item per line), located by the four corners of the whole block. When the style changes within the block, `data` shall be a list of runs; otherwise a plain string.
AC: Given WorkedExample4.pdf, When processed, Then exactly 2 paragraphs exist, the first with `data == "Claiming Joint Accounts"` at `{top 0.52, left 0.90, bottom 0.74, right 3.39}` in.
AC: Given WorkedExample5.pdf, When processed, Then 17 paragraphs exist, and the one beginning `"Any assets other than shares"` has `data` as a list of runs including `"Capital Bank and Trust Company"` in a Demi style.

**FR-LIST-001 — List items and checkboxes**
Any line introduced by a marker glyph (bullet, number, or checkbox character) shall be a list item, with the marker's code point as found in the PDF (not assumed to be a bullet), its style, the marker space, the content, and the four corners from the marker through the end of the content. Continuation lines belong to the item. A checkbox's state is expressed only by its glyph.
AC: Given WorkedExample4.pdf, When processed, Then 12 list items exist: 2 with `marker == "0x2610"` (MS Gothic 15pt) at left 0.90in, and 10 with `marker == "0x2022"` (Symbol MT 10pt) at left 1.20in with `marker-space == "0.19in"`.
AC: Given WorkedExample4.pdf, When processed, Then the list item at top 1.72in has `item-content` as two runs, the first `"Transfer/Registration Change Request"` in an italic style.

**FR-TABLE-001 — Tables**
When content is aligned in rows and columns, the skill shall report one table for that arrangement, row by row, with each cell's corners, style, background, borders, and content. A row has as many cells as are visible in it; a cell that covers more than one row or column carries `rowspan` or `colspan` and corners covering its whole merged extent. A cell may be a list item. Within one page, an aligned arrangement of rows and columns is one table; the skill does not divide it into smaller tables. Since every page is described on its own, a chart that continues across pages is one table per page.
Note on keeping groups together: a document may be *built* so that a group of rows does not break across a page — SBC does this, using a separate table per group in SmartCOMM — but that is a generation requirement, not a fact the page states (OOS-010), and it is not achievable everywhere: a group too large for one page breaks regardless, and then the page shows a split row (FR-TABLE-004).
AC: Given WorkedExample1.pdf, When processed, Then exactly 1 table exists at top 4.31in, left 0.75in, with 9 rows, whose first row has 2 cells `"Invoice/Notice Information"` and `"Contract Information"`.
AC: Given WorkedExample3.pdf, When processed, Then exactly 1 table exists whose first row has 9 cells beginning `"Transaction Date"`, `"Transaction Type"`, `"Location"`.
AC: Given WorkedExample5.pdf, When processed, Then a table exists whose second row has 2 `listitem` cells with `marker == "0xF071"` (`"Traditional IRA"`, `"SEP/SARSEP IRA"`).
AC: Given WorkedExample2.pdf, When processed, Then 5 tables exist (FR-TABLE-005).
AC: Given c4.pdf, When processed, Then page 1 has 3 tables, at tops 4.69in, 7.00in, and 9.49in, and page 2 has a table of 41 rows.
AC: Given SBC_Example_Data.pdf, When processed, Then the benefits chart on page 3 is one table with column boundaries at 0.20, 1.60, 3.71, 5.81, 7.92, and 10.73 in, not one table per benefits group.
AC: Given SBC_Example_Data.pdf, When processed, Then the header cell `"What You Will Pay"` has `colspan == 2`, with corners `{top 0.15, left 3.71, bottom 0.37, right 7.92}` in, and the row beneath holds `"In-network Provider (You will pay the least)"` and `"Out-of-network Provider (You will pay the most)"` as separate cells.
AC: Given SBC_Example_Data.pdf, When processed, Then the header cells `"Common Medical Event"`, `"Services You May Need"`, and `"Limits, Exceptions, & Other Important Information"` each have `rowspan == 2`, with corners spanning 0.15in to 0.78in.
AC: Given SBC_Example_Data.pdf, When processed, Then the column-1 cell `"If you have outpatient surgery"` has `rowspan == 2`, with corners spanning 0.78in to 2.00in, while columns 2–5 have a row boundary at 1.59in.
AC: Given SBC_Example_Data.pdf, When processed, Then a cell exists in the "Limits, Exceptions" column with `rowspan == 3` covering the three drug rows, and the header cells have `background == "#006699"`.

**FR-TABLE-002 — Cell corners**
Every cell shall carry its own four corners, taken from DocExtractor's boxes, so that no consumer has to derive a cell's position by adding up the rows above it. (In specReview's testing, approximate row heights compounded to put a row-9 box about 0.3in off; corners remove that failure mode.)
AC: Given WorkedExample1.pdf, When processed, Then every cell of the table has corners that enclose its own text, including the last row.

**FR-TABLE-003 — Borders, backgrounds, and shaded boxes**
Every cell shall carry its background color where it has one (e.g. SBC's `#006699` header and `#B7DEE8` / `#EBF6F9` body rows), taken from the fills DocExtractor reports beneath the cell, and `"none"` where it has none. Most tables have no visible lines: every cell has `borders: "none"` and the table has no `border`. When the table's outer edge is drawn, the table has one `border` value. When only some internal lines are drawn, they are recorded on the cells. A block of text on a shaded background that extends beyond the text or does not line up with a nearby table, or content inside a drawn box that does not line up with a nearby table, is its own table (usually 1 × 1) with the color on the cell.
AC: Given WorkedExample5.pdf, When processed, Then the checkbox table has `border == "1pt solid #000000"`.
AC: Given WorkedExample3.pdf, When processed, Then no cell has a `borders` value other than `"none"`.
AC: Given c4.pdf, When processed, Then page 1's table at top 9.49in has `border == "1pt solid #000000"`, and page 1 has cells with `background == "#CECFD1"` (the grey rectangles in DocExtractor FR-PATH-001).

**FR-TABLE-005 — Fill-in lines with captions**
A blank to be written on, with a caption beneath it, shall be reported as a table: one row holding the blank and one holding the caption, so that the caption stays aligned under its blank.
Rationale (why authors build them this way): a long signature line is often drawn as a table cell border rather than as a rule or an underline, because a rule or an underline is affected by the text around it, while a table lets the author place both the line and the caption below it exactly.
The blank itself may be underscore characters (WorkedExample2) or a line drawn as a cell border. A drawn line that has a caption below it but is not part of a column arrangement of blanks is a rule with a paragraph beneath it, not a table (WorkedExample5's signature lines). Deciding between them is judgment: DD-10.
AC: Given WorkedExample2.pdf, When processed, Then the blanks written as underscore characters and the captions beneath them (`"Name of Donor"`, `"Address"`) are reported as tables, not as paragraphs.
AC: Given WorkedExample5.pdf, When processed, Then the three lines at top 9.72in are rules and their captions are paragraphs, not a table.

**FR-TABLE-004 — Rows split across pages**
A row that begins on one page and resumes on the next shall be reported on both pages, marked `split: "start"` and `split: "end"`, with the same number of cells on both and the dimensions of the part shown on each page. On the second page, the continued row is its own table positioned where its content sits. All other rows are `split: "no"`.
AC: Given PastDue_0001.pdf, When processed, Then page 2's table (top 2.57in, left 1.00in) has 10 rows, of which the last is `split: "start"`, height 0.52in, with cells `"Statutory Disability New Jersey"` and `"SDJ0666666"`.
AC: Given PastDue_0001.pdf, When processed, Then page 3's table (top 1.02in) has 7 rows: the first is the `split: "end"` of that row, height 0.34in, with the same cell count and the same first two values; the last is a `split: "start"` for `"Basic Term Life"` / `"FLX0111111"`, height 0.70in.
AC: Given PastDue_0001.pdf, When processed, Then page 4's table has 3 rows, the first being that row's `split: "end"`, height 0.89in.
AC: Given PastDue_0001.pdf, When processed, Then every other row in the document is `split: "no"`.

**FR-RULE-001 — Rules**
Each divider or underline, whether a stroked line or a thin filled bar, that is not part of a table's borders shall be reported as a rule with all four edges and its color.
AC: Given WorkedExample3.pdf, When processed, Then 5 rules exist from left 0.14in to right 8.13in at tops 1.90, 2.41, 5.72, 6.08, 10.65 in.
AC: Given WorkedExample5.pdf, When processed, Then 3 rules exist at top 9.72in (signature lines).
AC: Given WorkedExample4.pdf, When processed, Then no rules exist.

**FR-IMAGE-001 — Images**
Each image shall be reported with a unique name and its four edges. An image that is a barcode is reported only as a barcode.
AC: Given WorkedExample5.pdf, When processed, Then 2 images exist, at `{top 0.25, left 0.57, bottom 1.30, right 1.40}` and `{9.13, 3.00, 9.72, 4.33}`.
AC: Given WorkedExample1.pdf, When processed, Then exactly 1 image exists.
AC: Given c4.pdf, When processed, Then every image `name` is generic (`IMAGE001`, `IMAGE002`, …) and every image has four edges. (The analyst may later extend a name as a hint to the author, as the SBC reference workbook does with `IMAGE001_LOGO`; the skill does not.) (c4.json uses descriptive `ref` names and width/height; comparisons use its extents only; OQ-15.)

**FR-BARCODE-001 — Barcodes**
Each DocExtractor barcode region shall be a barcode item, and the image, paths, or barcode-font text that draw it shall not also be reported as other items. A barcode is described in its native orientation: `top` and `left` of its native top-left corner, `height` of the bars, and `rotation`, the clockwise rotation about that corner that places it on the page. Linear barcodes (Code 39, IMB, and similar) have no `width`, since their length depends on the encoded data, and when a Code 39 barcode is produced from a text string in a barcode font its size cannot be determined at all; the document analyst sets the real size; QR and other 2-D codes report `width`. Barcodes are never decoded (DocExtractor BR-002).
AC: Given WorkedExample1.pdf, When processed, Then exactly 1 barcode exists at top 7.21in, left 7.99in, height 0.38in, `rotation == "90deg"`, with no `width`.
AC: Given barcodes.pdf, When processed, Then 3 barcodes exist, and only the QR code has a `width`.
AC: Given WorkedExample4.pdf, When processed, Then no barcode exists.

**FR-FORM-001 — Form controls**
Each form control DocExtractor reports shall be a `form_control` content item with its bounding box (four edges, in inches), its `control_type`, its declared `name`, and its `value` exactly as DocExtractor reports it. A control's value is a value like any other: text read from a form is no different from text recognized on the page, and an empty text box or an unchecked checkbox is a real answer. It is never reported as text, even when it holds a value, because the analyst has to know it is a control to write the code rules for it. It takes its place in reading order like any other item. A path in the page content that coincides with a control's box (the printed frame of a checkbox, for example) is accounted for as that control's frame and not reported separately. Controls whose form was flattened are ordinary page content and are not controls.
AC: Given fw9.pdf, When processed, Then page 1 has 23 `form_control` items: 15 `text` and 8 `checkbox`.
AC: Given fw9.pdf, When processed, Then a `checkbox` control exists at `{top 2.50, left 1.01, bottom 2.61, right 1.13}` in, and no rule or table is reported at that box.
AC: Given fw9_filled.pdf, When processed, Then page 1 has 23 `form_control` items, no paragraph contains `"PAT Q SAMPLE"`, and the control named `…f1_01[0]` has `value == "PAT Q SAMPLE"`.
AC: Given fw9.pdf (empty form), When processed, Then every `text` control has `value == ""` and every `checkbox` has `value == "Off"`.
AC: Given fw9_filled_flattened.pdf, When processed, Then no `form_control` items exist and `"PAT Q SAMPLE"` appears as text.
AC: Given WorkedExample1–5.pdf, When processed, Then no `form_control` items exist.

**FR-ROTATE-001 — Other rotated content**
Any other rotated item shall be described the same way: native top-left corner, native size, clockwise `rotation`. (DocExtractor reports rotation from the text matrix; its convention is DocExtractor DD-2, and this skill converts it to clockwise.)
AC: Given TestCase4.pdf, When processed, Then the item containing `"FITS"` has a `rotation` of `"90deg"` or `"270deg"` consistent with the clockwise convention.

**FR-TEXT-001 — Duplicate text**
Text drawn twice at the same position (stroke then fill, to simulate bold) shall be reported once, as one value, with a bold style (OQ-14).
AC: Given TestCase4.pdf, When processed, Then `"PERFECTLY"` appears exactly once on page 1.

**FR-HIDDEN-001 — Invisible text and printer marks**
Text that a reader cannot see (colored to match the background, 1 pt or smaller, or in an invisible rendering mode), including printer processing marks, shall be reported as an ordinary paragraph with its actual color and size, because its purpose cannot be determined from its content. It shall never be dropped. White text on a dark shape is visible and is also reported normally.
AC: Given TestCase4.pdf, When processed, Then a paragraph containing `"CUT THIS OUT FOR YOUR TAP HANDLE"` exists with white color.
AC: Given c4.pdf, When processed, Then page 1 has a paragraph at top 0.11in, left 0.49in, height ≈ 0.04in, whose `data` is `"JAN005237179"` (the text itself is subject to DocExtractor SCS-003: OCR may misread it), and a paragraph `"Confirm - Mail 1"` at top 0.07in, left 5.50in.

**FR-OCRBG-001 — Text inside raster areas on OCR pages**
On a page read by OCR, the skill cannot tell a picture from text that was rasterized, so text that OCR finds inside an image area shall be reported as text, not as an image. The text is reported on a background, using the shaded-box form (a table, usually 1 × 1; FR-TABLE-003), and the background color is written as `"see original document"` (BR-005): the color exists only in the image's pixels, and neither DocExtractor nor this skill determines it (OQ-17). An image area in which OCR finds no text remains an image.
Rationale: the skill cannot know from raster images whether an area was a picture or text. The document analyst will review these findings (for example, deciding that the scanned text was really an image) and supply the color.
AC: Given c4.pdf, When processed, Then page 6 has no image item; its text (7 raster strips from top ≈ 0.85in to 1.73in, left 0.68in, width ≈ 7.00in) is reported as text on a background whose color is `"see original document"`, never a guessed value. (The actual color is ≈ #387E7E green.)
(Page 1's image at top 1.90in, left 5.00in follows the same rule if OCR finds text in it; not yet checked.)

**FR-STYLE-001 — Style strings**
Every text-bearing item shall carry a style string built from the font name exactly as the PDF declares it, with any subset prefix removed (the prefix is an artifact of embedding, not part of the name), and the size in points: `"<PDF font name> <size>pt"`, e.g. `"AvenirNextLTCom-Demi 16pt"`. Nothing is added that the PDF does not state: no friendly family name, no separate weight or style word (a bold face is named as such by the PDF, e.g. `Arial-BoldMT`), and no role. The skill reports what it can extract from the PDF; where the analyst knows the document's real styling differs from what the PDF declares, it is theirs to call out. On OCR pages, where the font is unknown, the style shall be exactly `"see original document"` (BR-005): no font name, and no description of weight, size, or role, since none of these is reported by DocExtractor for OCR words. The measured size of the text is reported separately (FR-OCRHEIGHT-001).
AC: Given WorkedExample4.pdf, When processed, Then the first paragraph's style is the PDF's font name for it plus `" 16pt"`, with no subset prefix and no added weight word. (WorkedExample4.json's `"Avenir Next Demi 16pt"` is a friendly name and is not reproduced; SCS-002 does not compare styles.)
AC: Given c4.pdf, When processed, Then every style is exactly `"see original document"`. (c4.json adds qualifiers such as `(bold)` and `(large title)`; these are not reproduced, and SCS-004 does not compare styles.)

**FR-OCRHEIGHT-001 — Measured text height on OCR pages**
Because font size cannot be captured on an OCR page, every text-bearing item on such a page (paragraph, list item, table cell) shall carry `text-height`, in points rounded to the nearest 0.5 pt (e.g. `"8.5pt"`), matching how sizes are written in style strings. When the skill combines OCR words into lines and lines into items, each line's height is the height of the tallest word in that line, and the item's `text-height` is its tallest line height. When heights differ within a line or between lines by more than 0.5 pt (DD-8), the item shall also carry `mixed-heights: true` (FR-MIXED-001). `text-height` is labeled and treated as a measurement, not a font size. Items on digital pages do not carry `text-height`; their sizes are in the style strings and runs.
AC: Given c4.pdf, When processed, Then every paragraph, list item, and non-empty table cell on every page has a `text-height`.
AC: Given c4.pdf, When processed, Then the paragraph containing the printer mark at top 0.11in, left 0.49in has `text-height` between `"2pt"` and `"4.5pt"` (the mark is drawn about 3 pt tall; DocExtractor SCS-003).
AC: Given c4.pdf, When processed, Then the `text-height` of the paragraph `"Confirmation"` (top 0.47in) is greater than that of the paragraph `"12/22/25"` (top 1.20in).
AC: Given WorkedExample4.pdf, When processed, Then no item has a `text-height`.

**FR-MIXED-001 — Mixed text sizes**
Any text-bearing item whose text is not all one size shall carry `mixed-heights: true`, so that the document analyst is reminded to investigate (e.g. superscript text). On digital pages, sizes are the font sizes DocExtractor reports for each word, and two sizes differ when they differ by more than 0.5 pt, compared on DocExtractor's unrounded values. On OCR pages the rule is best effort, because a word box varies with the letters in it (OQ-19): lines are compared by line height (FR-OCRHEIGHT-001), and within a line a word counts as a different size only when its height differs from the line height by more than 0.5 pt *and* its bottom sits above, or its top sits below, the rest of the line by more than 0.5 pt (a superscript is smaller and raised; a subscript smaller and lowered). The aim is to keep noise down: a reminder that fires on most rows is not a reminder. A list item's marker is not compared with its text. Items with one size carry no `mixed-heights` key.
AC: Given WorkedExample4.pdf, When processed, Then no item has `mixed-heights` (its 15 pt checkbox markers are not compared with their 14 pt text).
AC: Given c4.pdf, When processed, Then fewer than 10% of text items have `mixed-heights: true`. (Best-effort noise check; the exact threshold is a proposal to be tuned against real DocExtractor output.)
AC: None yet for a digital superscript: no test document has one (OQ-9).

**FR-ORDER-001 — Reading order**
Content items shall be listed in the order their top-left corners are reached moving down the page (for a rotated barcode, as specScan step 5 describes).
AC: Given WorkedExample4.pdf, When processed, Then the `top` values of the content items are non-decreasing.

**FR-BOX-001 — Bounding boxes on every leaf item**
Every leaf item shall carry its four corners, so that a box can be drawn around it without deriving anything. The one exception is a barcode: it has top, left, height, and rotation, and a width only for 2-D codes, because a linear barcode's length depends on data it does not have (FR-BARCODE-001).
AC: Given any worked example, When processed, Then every leaf item has the fields listed above.

**FR-DIAG-001 — Unrecognized content (Rule 0)**
The skill shall never guess, and what it reports depends on what DocExtractor gave it:
- **A value with no classification.** When DocExtractor extracted text but the skill cannot decide what the text is beyond text (not a paragraph in a block, not a list item, not part of a table), the skill shall report it as a `paragraph`: at minimum it is known to be text, at a location, with a style.
- **A located item with no value.** When DocExtractor identified something but could not extract a value from it (an empty value at low confidence), the skill shall report an `unrecognized` item at that location, since nothing more can be said about it. These are reported in place, in reading order, not collected into a separate list.
- DocExtractor does not report a blob it cannot resolve to anything at all, so nothing reaches the skill for those.
DocExtractor warnings are carried forward.
AC: Given any test PDF, When processed, Then every primitive in the extraction record is part of a content item, part of the page background or a table border, or reported as an `unrecognized` item.
AC: Given c4.pdf, When processed, Then any OCR word with an empty value is reported as an `unrecognized` item at its location, never as a paragraph with empty text.

# 7. Non-functional Requirements

**NFR-1 — Performance**
No requirements. (DocExtractor may take up to about a minute per OCR page.)

**NFR-2 — Scalability / Isolation**
No shared state between invocations.

**NFR-3 — Environment**
Runs as a Claude skill on the same machine as DocExtractor. Which grouping steps are scripts and which are model judgment: DD-1.

**NFR-4 — Determinism**
Run-to-run variation in grouping is allowed, because grouping is judgment, but it is never silent: each run writes a new version (FR-VER-001) and any two versions can be compared (FR-VER-002). Measurements taken from the extraction record do not vary. The `version` block (number, based_on, origin, created) is excluded from this comparison. Where variation does occur, versioning (FR-VER-001, FR-VER-002) makes it visible rather than silent.

**NFR-5 — Language**
Inherits DocExtractor NFR-5.

**NFR-6 / NFR-7 — Security and Privacy**
See LIM-001. The model that runs this skill sees the document's text, so it shall neither retain that text nor allow it to be used for training. A model running locally satisfies this by construction; a hosted model satisfies it only under terms that say so, and only once that has been verified and recorded (OQ-12). DocExtractor retains nothing; this skill's output files (the JSON versions and the extraction record) contain the document's text, including any PII, and are written only beside the input PDF. They carry the same sensitivity as the PDF, and protecting them is the end user's responsibility (Intent, Security).

**NFR-8 — Reliability**
No stated requirements.

**NFR-9 — Error handling**
Never fails on input that meets DocExtractor IF-002; returns what it could structure and reports the rest under Rule 0.

**NFR-10 — Observability**
FR-DIAG-001.

**NFR-11 — Portability**
The output is independent of any document-generation system (specScan description).

**NFR-12 — Maintainability**
specScan expects its instructions to be updated as new kinds of content are met (Rule 0). The same applies here: each unrecognized-content report is a candidate for a new rule.

**NFR-13 — Consumability**
Readable by a person as well as an agent: self-describing keys, inches, human-readable style strings.

# 8. Business Rules

**BR-001 — Layout, never business meaning**
The skill describes layout only. This is a consequence of separating extraction from specScan: working only from DocExtractor output, the skill does not have the context to do more than describe layout and give items generic names. It shall not label content by business meaning (address, account number, signature, logo, header) and shall not infer the type of document. (This is why specScan's `documentName` is dropped; OQ-3.)

**BR-002 — Never guess** (specScan Rule 0)
When the skill cannot recognize or describe something, it says so, with the location. It never substitutes a plausible value.

**BR-003 — Nothing silently dropped**
Every DocExtractor primitive is accounted for (FR-DIAG-001). Invisible content is reported, not removed (FR-HIDDEN-001).

**BR-004 — DocExtractor is the only source of facts**
The skill converts units and groups primitives; it does not re-measure the PDF (IF-003).

**BR-005 — "see original document"**
Any value the skill could not see or could not resolve (a font on an OCR page, a background color inside a raster image, and similar) shall be written as exactly the string `"see original document"`: no qualifier, never `null`, never a guessed value. This gives the document analyst one consistent signal: the tool had nothing reliable to report here. Measurements the tool *can* make are reported in their own fields (e.g. `text-height`), not added to this string.

**BR-006 — One PDF instance, many versions**
Every output belongs to exactly one PDF instance (FR-PDFID-001). A changed PDF means new outputs; moving an analyst's work from outputs for one PDF instance to outputs for another is a manual task (a future tool: OOS-008). Within one PDF instance, outputs are never overwritten: each run and each analyst correction is a new version (FR-VER-001).

# 9. Non-Goals / Out of Scope

**OOS-001** — Identifying variable data (fields): future Dynamic Data project.
**OOS-002** — Business meaning of content items (BR-001).
**OOS-003** — OCR of text inside images on pages that have a text layer (DocExtractor OOS-005), e.g. the "CREAM Ale" title in TestCase4.pdf.
**OOS-004** — Decoding barcodes or identifying symbology beyond linear vs. 2-D.
**OOS-005** — Producing input for any particular document-generation system.
**OOS-006** — Running the Mapping skill.
**OOS-007** — A tool that compares two versions and reports the differences. This release only guarantees that versions are kept and comparable (FR-VER-002).
**OOS-008** — Carrying outputs or analyst work from one PDF instance to another (e.g. a revised document). Future tool.
**OOS-009** — Annotations. They were added to the PDF after the document was produced, and this spec describes the document, not the review of it. DocExtractor no longer reports them at all (its FR-ANNOT-001, v0.9), so nothing reaches this skill. Caveat: an annotation that was flattened into the page is page content and can no longer be told apart (DocExtractor OOS-008).
**OOS-010** — Generation requirements: the rules a document must follow when it is rebuilt, as opposed to what this page happens to show. They arrive in layers — corporate (branding, accessibility), department (a group that produces statements must keep the sheet count down, while marketing may add offers on separate sheets), and document — and none of them is written in the PDF. A page shows one outcome of those rules, not the rules, and often cannot distinguish a deliberate outcome from a coincidence.
Worked example, row groups: the prevailing custom is that a grouped set of rows stays together on a page, but a group too large to fit has to split, and then the continuation on the next page usually needs a header that makes clear what carried over. The skill can report that a row split (FR-TABLE-004) and what each page shows; it cannot report that the rule existed. The analyst supplies these requirements.

# 10. Limits / Constraints

**LIM-001 — No exfiltration, no training**
DocExtractor's processing is local and makes no network connections (DocExtractor LIM-001). For this skill the requirement is that the document's content is neither retained outside the user's own files nor used to train any model. Running the model locally is one way to meet it; any other arrangement must be shown to meet it (OQ-12).

**LIM-002 — PDF only**

# 11. Product Success Metrics

**SCS-001** — All acceptance criteria in §6 pass.
**SCS-002** — For each of WorkedExample1–5.pdf, the output matches the JSON (ignoring `documentName`) in content item types and counts, and in every location and size within 0.02 in, after converting the JSON's `width`/`height` to corners (`right = left + width`, `bottom = top + height`). Style strings are not compared: the worked examples use friendly font names, while this skill reports the PDF's own (FR-STYLE-001). (Same as DocExtractor SCS-002.)
**SCS-003** — The Mapping skill, given this skill's output for WorkedExample1 and WorkedExample5, boxes every leaf item correctly with no manual fixes to the JSON.
**SCS-004** — On c4.pdf, the output matches `testCases/JanusSamples/c4.json` in content item types and counts and, after the same conversion as SCS-002, in location and size (tolerance to be confirmed), except that image names and styles are not compared (OQ-15, FR-STYLE-001), `text-height` is not compared (c4.json does not have it), and page 6 is expected to differ from c4.json (FR-OCRBG-001).

# 12. Deferred Decisions (design)

**DD-1** — Which steps are deterministic code (line and column clustering, unit conversion) and which are model judgment.
**DD-2** — Reading-order tie-breaks for items with equal tops and multi-column layouts.
**DD-3** — How close to full-page a fill must be to count as page background.
**DD-4** — Thickness below which a filled rectangle is a rule.
**DD-5** — Paragraph-break rule (line spacing, indentation, style change).
**DD-6** — How per-cell borders are written (specScan says "CSS2 formatted" but gives no example).
**DD-7** — *Decided v0.3:* unknown values are written as exactly `"see original document"` (BR-005).
**DD-8** — *Decided v0.3:* line height = the tallest word in the line; an item's `text-height` = its tallest line; mixed sizes are flagged with `mixed-heights`, not split into runs. Tolerance: 0.5 pt, the resolution document generators work with. It is stated in points, not pixels, because pixels depend on the OCR render resolution (DocExtractor DD-6): 0.5 pt is about 2 px at 300 dpi and about 4 px at 600 dpi.
**DD-9** — Canonical JSON form for FR-VER-002 (indentation, key order per item type, number formatting), and file naming for the extraction record (FR-EXTRACT-001).
**DD-10** — How to tell a fill-in-line table (FR-TABLE-005) from a rule with a caption beneath it.

# 13. Open Questions

- **OQ-1** — *Resolved v0.2:* specScan's SKILL.md defines the format. Should a copy of it be kept in this repository (e.g. `reference/specScan_SKILL.md`) so the PRS does not depend on another project's folder?
- **OQ-2** — *Resolved v0.2:* PDF file in, JSON written beside it (IF-001). *Amended v0.3:* the JSON is versioned, `<name>.v<N>.json` (FR-VER-001).
- **OQ-3** — *Resolved v0.3:* `documentName` is dropped. It was an aspirational field; the tools do not have the data needed to set it (§5.1).
- **OQ-4** — *Resolved v0.3:* the style string is the PDF's own font name (subset prefix removed) plus the size in points (FR-STYLE-001). Weight and style are whatever the font name says; nothing is translated into a friendly family name.
- **OQ-5** — *Resolved v0.3:* confidence stops at DocExtractor. The Structure JSON carries no confidence values; its readers (the document analyst and the Mapping skill) do not act on them, and a Consuming Application that wants values and confidence reads the saved extraction record (FR-EXTRACT-001). Unresolved values are marked `"see original document"` (BR-005).
- **OQ-6** — *Resolved v0.3 (from c4.json; please confirm):* printer marks do not count toward margins (FR-MARGIN-001). Other invisible text is assumed to follow the same rule.
- **OQ-7** — *Resolved v0.3:* form controls are reported as `form_control` items (FR-FORM-001); annotations are not reported at all (OOS-009). Anything that is not part of the original PDF, as far as that can be determined, stays out of the structure. *Knock-on, applied:* DocExtractor_PRS.md v0.9 now excludes annotations entirely, since nothing that was added to the PDF after the document was produced should be reported.
- **OQ-20** — *Resolved v0.3:* yes. A form control carries its `value`; a value read from a form is a value like a string or number recognized from page text (FR-FORM-001).
- **OQ-8** — *Resolved v0.2:* linear barcodes have no width; 2-D codes do (FR-BARCODE-001).
- **OQ-9** — Test corpus gaps. (a) *Resolved v0.3:* the expected output for c4.pdf is `testCases/JanusSamples/c4.json`; it has not had a second review pass. (`testCases/structure_c4.pdf.json` is unrelated testAgent output.) (b) *Resolved v0.3:* SBC_Example_Data.pdf covers merged cells (19 `rowspan` cells, no `colspan`) and PastDue_0001.pdf covers rows split across pages (two of them, pages 2→3 and 3→4). Both have reference JSONs, though see OQ-22. (c) TestCase1.pdf and TestCase5.pdf have no stated purpose. The remaining gaps are addressed by the purpose-built specimens in TestSet_PRS.md rather than by finding more sample documents.
- **OQ-10** — *Resolved v0.3:* the table is intended (FR-TABLE-005). Authors build a long signature or fill-in line as a table because a rule or an underline is affected by the surrounding text, while a table positions the line and its caption exactly.
- **OQ-11** — *Resolved v0.3:* variation is allowed but must be visible. Each run creates a new version of the outputs, and versions can be compared (NFR-4, FR-VER-001, FR-VER-002).
- **OQ-12** — *Resolved in principle v0.3:* the requirement is that the document's content is not retained outside the user's files and is never used to train a model (LIM-001, NFR-6/7). A local model meets it by construction. *Still to settle:* whether a hosted model under no-retention, no-training terms is acceptable, and what evidence records that it was verified.
- **OQ-13** — *Resolved v0.3:* unrecognized content is reported in place, not in a list (FR-DIAG-001): a value with no classification becomes a `paragraph`; an item with a location but no value becomes an `unrecognized` item. *Knock-on, applied:* DocExtractor_PRS.md v0.10 changes FR-OCR-002 to match — a mark it cannot resolve to text is not reported, and a text region it cannot read comes back with an empty value at low confidence.
- **OQ-14** — *Resolved v0.3:* one copy of the value, reported bold (FR-TEXT-001).
- **OQ-15** — *Resolved v0.3:* images have four edges and generic names (`IMAGE001`…). c4.json's descriptive `ref` names came from specScan, which had context the Structure skill does not (BR-001).
- **OQ-16** — *Resolved v0.3:* on an OCR page, text inside an image area is reported as text on a colored background (FR-OCRBG-001). c4.json's single image on page 6 is superseded.
- **OQ-17** — *Resolved v0.3 (option c):* the background color is reported as unknown. Determining a "dominant" color from pixels is unreliable (e.g. shading under characters to make text look like it is floating), and the document analyst must review these areas anyway. The original question was: where does the background color in FR-OCRBG-001 come from? On c4 page 6 the green (≈ #387E7E) exists only in the pixels of the raster images; the page's vector fills are white. DocExtractor reports nothing about an image's content (DocExtractor FR-IMAGE-001), and this skill does not look at the PDF (IF-003), so as written neither can supply the color. Options: (a) DocExtractor reports a background (dominant) color for each image, or for each OCR word's surroundings (a change to DocExtractor_PRS.md); (b) this skill samples the rendered page for that one purpose (an exception to IF-003); (c) the color is reported as unknown (Rule 0) and FR-OCRBG-001's AC drops the color.
- **OQ-18** — *Resolved v0.3:* `text-height` is written in points to 0.5 pt (e.g. `"8.5pt"`), since that is what authors use in styles. (Inches to 0.01 in, 0.72 pt, would be coarser than the 0.5 pt that matters.)
- **OQ-19** — *Resolved v0.3 (option b, best effort):* a word counts as a different size only when it is smaller *and* raised or lowered relative to its line (FR-MIXED-001). AFP-to-PDF conversions give limited information; the goal is to keep noise down. The original question: word boxes vary with the letters in them. An OCR word box spans the word's ink, so at the same font size `"mom"` (no ascenders or descenders) is noticeably shorter than `"Typography"`, often by more than 0.5 pt. Comparing word heights directly would mark most lines of ordinary text as mixed. Options: (a) compare line heights only, which misses a superscript within a line; (b) compare words only when their tops and bottoms are both offset (a superscript is small *and* raised); (c) accept the noise, since the flag is only a reminder. Needs a decision, ideally tested on c4.pdf.
- **OQ-21** — *Resolved v0.3:* no. Start indent, margin, padding, and alignment are not reported: a PDF does not state them, so any value would be a derived guess. The skill reports what it can extract — the font name and size the PDF declares, and the spacing that is visible in the output already (locations, widths, heights, row heights, marker space). If the analyst knows the document's real layout properties differ, it is theirs to call out.
- **OQ-22** — *Resolved v0.4.* The two newest reference JSONs (`SBC_Example_Data.json`, `PastDue_0001.json`) came from specScan before this project and do not agree with each other or with this spec. Decisions:
  - **Four corners, not width/height.** specScan's top-left-plus-size form suited one step that measured and interpreted together. With extraction split out and OCR involved, every item and cell reports `{top, left, bottom, right}` (FR-BOX-001, FR-TABLE-002). SBC's per-cell `height` and the row `height` both disappear; `props` keeps only `split`.
  - **Units.** Lengths stay strings with the unit (`"0.16in"`), as in PastDue and the worked examples, not bare numbers as in SBC.
  - **`colspan` is kept.** SBC has both kinds of merge; its JSON simply failed to record the `colspan` (FR-TABLE-001).
  - **One table per arrangement, per page.** SBC's JSON has a table per row group because that is how SmartCOMM keeps a group from breaking across a page. That is a requirement for the rebuilt document, not something the page states, and it does not hold everywhere — a group too large for a page breaks anyway. The skill reports the arrangement it sees: one table per page (FR-TABLE-001).
  - **Cell backgrounds are reported** wherever they can be determined (FR-TABLE-003).
  Consequence: `SBC_Example_Data.json` is reference material, not expected output. `PastDue_0001.json` matches this spec apart from the geometry change and the missing `props` on unsplit rows.
