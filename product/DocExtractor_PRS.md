---
# Product Requirements Specification — DocExtractor
**Status:** Draft v0.10 — 2026-09-22 (v0.10: OCR no longer reports unresolvable marks as junk words — either nothing, or an empty value at low confidence (FR-OCR-002, DD-7); v0.9: §0 components corrected to DocExtractor, Structure, Mapping; annotations removed from scope — nothing that was added to the PDF after the document was produced is reported (FR-ANNOT-001, OOS-007); v0.8: named DocExtractor; every form control scored; empty value is a value; XFA excluded; c4.pdf confirmed as AFP case; all open questions resolved)
---

# Related Intent Document
**Intent Document:** [intent/Intent.md](intent/Intent.md)

# 0. Context

DocExtractor is the first of three components that replace the monolithic `specScan` skill:

1. **DocExtractor (this spec)** — a tool. Reports what a single PDF page *contains*.
2. **Structure skill** — derives what the contents *mean* (paragraphs, lists, tables, rules, margins, barcodes-as-content, invisible printer marks) and produces the `specScan` JSON.
3. **Mapping skill** — numbers every item on the page, draws a box on each, and gives a person a workbook to record what each item depends on (it replaces the `specReview` skill).

A consumer that wants only part of the output (for example, just a list of every location where content was found) states that in a data contract given to the calling skill. DocExtractor itself always returns its complete, fixed output (OOS-006).

The dividing line between 1 and 2 is the governing principle of this spec: **DocExtractor reports what the PDF contains; it never decides what anything means** (BR-001). The one deliberate exception is barcode regions (FR-BARCODE-001).

# 1. Purpose & Scope

DocExtractor receives a PDF and returns an inventory of every primitive on its first page — text, vector paths, raster images, and barcode regions — with position, size, style, and paint order, plus a per-primitive confidence where one is meaningful. When the page has no text layer, DocExtractor falls back to OCR.

In scope: everything a page draws. Out of scope: any interpretation of what was drawn (see §9).

# 2. Glossary / Ubiquitous Language

The word **field** is reserved for a variable-data slot in a document, which is a separate, future project. It is not used by DocExtractor.

- **page**: the first page of the input PDF.
- **primitive**: one thing the page contains. Exactly one of: `word`, `path`, `image`, `barcode_region`, `form_control`.
- **word**: a maximal sequence of non-whitespace glyphs on one baseline, drawn with the same font, size, color, and rendering mode, and in the same paint operation. A change in any of these splits the word. (Granularity: see OQ-3.)
- **glyph**: a single drawn character. A glyph has a Unicode value when the font maps it, and always has a raw character code.
- **path**: a vector drawing operation — straight line, rectangle, or curve — with its stroke and/or fill.
- **image**: a raster image placed on the page.
- **barcode region**: an area of the rendered page whose appearance matches a barcode pattern, regardless of how it was drawn (raster image, vector paths, or text in a barcode font). Never decoded.
- **form control**: an interactive form widget declared in the PDF's form (AcroForm) — text box, checkbox, radio button, list or combo box, signature, or push button. The PDF itself declares these, so reporting them is not interpretation. A blank line drawn on the page for handwriting (e.g., `DATE BREWED ______`) is not a form control; it is words and paths. The term avoids "form field" because *field* is reserved (see above).
- **paint order**: the sequence in which the page draws its primitives. A primitive with a higher paint order is drawn on top of one with a lower paint order.
- **rendering mode**: the PDF text-rendering mode (fill, stroke, fill+stroke, invisible, clip variants).
- **extraction method**: how a word was obtained — `digital` (read from the PDF's text layer) or `ocr` (recognized from a rendered image of the page).
- **confidence score**: a value in [0.0, 1.0] expressing the quality of one primitive's extraction.
- **threshold**: a value in [0.0, 1.0] supplied by the caller; the minimum acceptable confidence.
- **scored primitive**: a primitive that carries an extracted *value* and therefore a confidence: every word, and every form control. For a form control, an empty value is still a value — an empty text box or an unchecked checkbox is a real answer — so every control is scored. A blank area of the page, by contrast, produces no primitive and is not counted. Paths, images, and barcode regions are located but carry no value, so they are not scored.
- **count at threshold**: the number of scored primitives whose confidence is greater than or equal to the threshold.
- **overall confidence**: the sum of the confidence values of all scored primitives. A consumer that wants the average divides by the scored count. Purpose: a consumer expecting a known number of values (e.g., five, three of them critical) uses the count at threshold and the overall confidence to decide between "the values may be there; check each one" and "the results are too poor to use".
- **page coordinates**: points (1/72 inch), origin at the top-left corner of the page, x increasing rightward, y increasing downward.

# 3. Users

## Persona 1: Structure skill (primary)
- Role: an LLM-driven skill that consumes DocExtractor's output.
- Problem statement: needs a complete and faithful inventory of what the page draws — including hidden, overlapping, rotated, and duplicate content — so that it can derive document structure without re-reading the PDF, and without DocExtractor having pre-judged what is significant.

## Persona 2: Consuming Application (test harness, pipeline)
- Role: code that invokes DocExtractor directly.
- Problem statement: needs to know how much of the page was extracted and how reliably, as a count against a threshold it controls.

## Persona 3: Mapping skill
- Role: a skill that draws numbered boxes on the page at the location of each item and ties each box to a row in a spreadsheet, where a person records how to obtain the data for it.
- Problem statement: needs the location of everything that may need data or special handling — including barcode regions and form controls, which carry no extracted value — so that no box is missed.

# 4. User Stories

**US-001**: As the Structure skill, I want every primitive on the page with its position, size, style, and paint order, so that I can derive paragraphs, lists, tables, rules, and margins.

**US-002**: As a Consuming Application, I want the text of every word with a per-word confidence, and a count of words that meet my threshold, so that I can judge whether the extraction is usable.

**US-003**: As the Structure skill, I want to know where barcodes are on the page regardless of how they were drawn, so that I can describe them as barcodes rather than as images, paths, or text — without anyone decoding them.

**US-004**: As a Consuming Application, I want pages that are only raster images (e.g., AFP converted to PDF) to still yield words, so that scanned and converted documents are not empty.

# 5. External Interface

The interface is part of the requirements because it is the contract every consumer depends on. Library and algorithm choices are design and do not appear here.

**IF-001 — Entry point**
A single Python function that accepts the PDF as bytes and a threshold, and returns the output as bytes: UTF-8 encoded JSON conforming to §5.1.
Proposed signature: `extract_page(pdf: bytes, threshold: float = 0.0) -> bytes`.
The default threshold of 0.0 counts every scored primitive.
Rationale: passing bytes keeps DocExtractor free of file-system state (NFR-2) and is why the input is a single page — the Consuming Application splits large documents and passes one page at a time.

**IF-002 — Preconditions**
The caller guarantees the input is a readable PDF containing at least one page. Behavior for any other input (null, corrupt, non-PDF, zero pages, password-protected) is unspecified. DocExtractor is not required to detect these conditions.

## 5.1 Output (logical schema)

Key names are proposed; exact spelling is deferred to design (DD-1), but every item below must be present.

```
{
  "schema_version": "0.2",
  "source_page_count": <int>,              // pages in the input PDF; only page 1 is extracted
  "page": { "width": <pt>, "height": <pt>, "rotation": <0|90|180|270> },
  "extraction_method": "digital" | "ocr",  // page level; see FR-OCR-001
  "threshold": <float>,
  "summary": {
    "word_count": <int>, "path_count": <int>, "image_count": <int>, "barcode_region_count": <int>,
    "form_control_count": <int>,
    "scored_count": <int>,
    "count_at_threshold": <int>,
    "overall_confidence": <float>          // sum; 0.0 when scored_count == 0
  },
  "primitives": [ <primitive>, ... ],       // sorted by paint_order
  "warnings": [ { "code": <string>, "message": <string>, "primitive_ids": [<id>, ...] }, ... ]
}
```

Every primitive has: `id` (unique within the output), `kind`, `paint_order`, `bbox` {`x0`,`top`,`x1`,`bottom`} in page coordinates, and `confidence` (float or null).

- **word** adds: `text` (Unicode), `glyph_codes` (raw character codes, in order), `unmapped_glyphs` (bool), `font` (name exactly as in the PDF, including any subset prefix), `size` (pt), `color` (see FR-COLOR-001), `rendering_mode`, `rotation` (degrees, derived from the text matrix), `baseline` (y), `extraction_method`.
- **path** adds: `segments` (`line` | `rect` | `curve`, with points), `stroke` (color or null), `stroke_width`, `dash` (or null), `fill` (color or null).
- **image** adds: `rotation` (from the placement matrix). Nothing about the image's content is reported — only that an image occupies that space.
- **form_control** adds: `control_type` (`text` | `checkbox` | `radio` | `choice` | `signature` | `button`), `name` (fully qualified name as declared), `value` (current value as declared: `""` for an empty text or choice control; for checkboxes and radio buttons, the name of the current state, e.g. `"Off"` for not checked. `null` only when the value cannot be determined, per BR-004), `options` (for choice controls), `read_only` (bool), `required` (bool).
- **barcode_region** adds: `overlaps` (ids of the primitives that draw it; may be empty), `detection_basis` (`raster`, `vector`, `text`, or `unknown`), `detection_confidence` (the detector's confidence that the region is a barcode; not a value confidence, so `confidence` is null).

## 5.2 Test corpus

| File | Pages | What it exercises |
|---|---|---|
| WorkedExample1.pdf / TestCase1.pdf | 1 | Digital letter; raster barcode image; grey shaded rectangle; underlines |
| WorkedExample4.pdf | 1 | Digital text only; symbol-font checkboxes and bullets; no paths |
| TestCase4.pdf | 2 | Rotated text; text drawn twice (stroke + fill); white text on a dark shape; text inside a raster image; first-page rule |
| c4.pdf | 6 | AFP document converted to PDF. No text layer (OCR); 98 raster text fragments; vector rules and shading; icons that OCR cannot resolve to text (FR-OCR-002) |
| fw9.pdf | 6 | Empty fillable form (AcroForm + XFA); checkbox group sharing one field name; comb fields |
| fw9_filled.pdf | 6 | fw9.pdf with 8 text controls filled and one checkbox checked; XFA removed |
| fw9_filled_flattened.pdf | 6 | fw9_filled.pdf flattened: no controls, values become page content |
| annotations.pdf | 1 | WorkedExample4.pdf plus annotations that must all be ignored (a comment, a text-box comment, a stamp, a link, a reviewer highlight, an ink drawing) and an "original" highlight drawn in the page content, which must still be reported as a path |
| barcodes.pdf | 1 | Code 39 as vector rectangles; QR code as vector squares; Code 39 as text in a barcode font; a striped decoy that is not a barcode |

Test data in the fw9 fixtures is fictional (name "PAT Q SAMPLE", SSN 000-00-0000). `make_fixtures.py` rebuilds the four generated files from the originals.

# 6. Functional Requirements

Positional tolerance for all acceptance criteria: ±0.5 pt unless stated.

**FR-PAGE-001 — Page geometry**
The system shall report the page width, height, and rotation.
AC: Given TestCase1.pdf, When extracted, Then `page.width == 612` and `page.height == 792` and `page.rotation == 0`.

**FR-PAGE-002 — First page only**
When the input contains more than one page, the system shall extract only the first page and report the input's page count.
AC: Given TestCase4.pdf (2 pages), When extracted, Then `source_page_count == 2` and no word has text `"RECIPE"` (page-2 content).
AC: Given c4.pdf (6 pages), When extracted, Then `source_page_count == 6` and no word has text `"EUROPEAN"` (first appears on page 2).

**FR-COORD-001 — Coordinate system**
All positions shall be reported in page coordinates (§2), unrounded or rounded no coarser than 0.01 pt.
AC: Given TestCase1.pdf, When extracted, Then an image exists with `bbox == {x0: 53, top: 44, x1: 228, bottom: 79}`.

**FR-TEXT-001 — Words**
When the page has a text layer, the system shall return every glyph on the page as part of exactly one word, with the attributes in §5.1.
AC: Given WorkedExample1.pdf, When extracted, Then a word exists with `text == "JEFFREY"`, `x0 == 73.0`, `font` containing `"DejaVuSans-Bold"`, `size == 8.0`.
AC: Given WorkedExample4.pdf, When extracted, Then a word exists with `text == "Transfer/Registration"` and `font` containing `"AvenirNextLTCom-It"`.
AC: Given any digital test PDF, When extracted, Then the total glyph count across all words equals the page's glyph count reported by an independent tool (excluding whitespace glyphs; see OQ-3).

**FR-TEXT-002 — Raw glyph codes and symbol fonts**
Every word shall carry both its Unicode text and its raw glyph codes. Where a glyph has no Unicode mapping, `unmapped_glyphs` shall be true and a warning shall be emitted. The system shall not substitute or guess characters.
AC: Given WorkedExample4.pdf, When extracted, Then exactly two words have `text == "\u2610"` with `font` containing `"MS-Gothic"` and `size == 15`.
AC: Given WorkedExample4.pdf, When extracted, Then ten words have `text == "\u2022"` with `font` containing `"SymbolMT"`.

**FR-TEXT-003 — No filtering**
The system shall report all text regardless of color, size, rendering mode (including invisible), position (including off-page), or what is drawn over or under it.
AC: Given TestCase4.pdf, When extracted, Then words `"CUT"`, `"THIS"`, `"OUT"`, `"FOR"`, `"YOUR"`, `"TAP"`, `"HANDLE"` exist with color white.

**FR-TEXT-004 — No merging of duplicates**
When the same text is drawn more than once (e.g., once stroked and once filled to simulate bold), the system shall report each drawing as separate words with their own rendering mode and paint order.
AC: Given TestCase4.pdf, When extracted, Then the word `"PERFECTLY"` appears twice with identical bbox, once with a stroke rendering mode and once with fill.

**FR-TEXT-005 — Rotated text**
The system shall report each word's rotation derived from its text matrix. Words shall not be re-ordered or re-oriented.
AC: Given TestCase4.pdf, When extracted, Then the word `"FITS"` has `rotation` of 90 or 270 (convention: DD-2) and a bbox inside `{x0: 574, top: 535, x1: 586, bottom: 732}`.

**FR-COLOR-001 — Color**
Every color shall be reported as its PDF color space, its raw components, and a derived sRGB hex value.
AC: Given TestCase1.pdf, When extracted, Then a path exists with `fill.hex == "#CCCCCC"` and `stroke == null` and bbox `{x0: 54, top: 478, x1: 254, bottom: 490}`.
AC: Given WorkedExample4.pdf, When extracted, Then word colors report color space DeviceGray with components `[0]` and hex `#000000`.

**FR-PATH-001 — Vector paths**
The system shall report every stroked or filled vector path with the attributes in §5.1.
AC: Given TestCase1.pdf, When extracted, Then exactly two stroked horizontal line paths exist near y = 335–336, from x ≈ 53 to 173 and x ≈ 309 to 404, each with stroke width ≈ 0.44 pt and black stroke.
AC: Given WorkedExample4.pdf, When extracted, Then `path_count == 0`.
AC: Given c4.pdf, When extracted, Then 9 filled rectangle paths exist, 7 of them white and 2 grey (≈ #CECFD1) at `{57, 349, 362, 365}` and `{57, 515, 362, 531}`; and 42 line paths exist. Paths on an OCR page are still read from the PDF (`digital`), not recognized.

**FR-IMAGE-001 — Images**
The system shall report the location of every raster image placed on the page, with the attributes in §5.1, and nothing about its content.
AC: Given TestCase1.pdf, When extracted, Then exactly two images exist: one at `{53, 44, 228, 79}` and one at `{575, 434, 602.5, 519}`.
AC: Given c4.pdf, When extracted, Then `image_count == 98` (each run of text on this page is its own small raster image).

**FR-ORDER-001 — Paint order**
Every primitive shall carry a paint order consistent with the order in which the page draws it.
AC: Given TestCase4.pdf, When extracted, Then the filled dark path with bbox ≈ `{431, 323, 576, 370}` has a lower `paint_order` than the white word `"CUT"`.

**FR-BARCODE-001 — Barcode regions**
The system shall identify areas of the rendered page that visually match a barcode pattern, regardless of whether they are drawn as a raster image, as vector paths, or as text in a barcode font. For each, it shall report the region's bbox, a detection confidence, the detection basis, and the ids of overlapping primitives. The underlying primitives shall still be reported in their own right.
AC: Given TestCase1.pdf, When extracted, Then exactly one barcode region exists with bbox within 2 pt of `{575, 434, 602.5, 519}`, and its `overlaps` includes the id of the image at `{575, 434, 602.5, 519}`.
Negative AC: Given WorkedExample4.pdf, When extracted, Then `barcode_region_count == 0`.
AC: Given barcodes.pdf, When extracted, Then exactly three barcode regions exist:
- one within 3 pt of `{90, 124, 225, 160}` with `detection_basis == "vector"` (Code 39 bars);
- one within 3 pt of `{84, 232, 160, 308}` with `detection_basis == "vector"` (QR code);
- one whose `overlaps` includes the word `"*TEST1234*"` (font containing `"LibreBarcode39"`), with `detection_basis == "text"`.
Negative AC: Given barcodes.pdf, When extracted, Then no barcode region overlaps the decoy stripes at `{72, 460, 210, 490}`.
AC: Given barcodes.pdf, When extracted, Then all 236 filled rectangles that draw the barcodes and the decoy are reported as paths (BR-003), and `"*TEST1234*"` is reported as a word.

**FR-OCR-001 — OCR fallback**
When the page's text layer contains no glyphs, the system shall render the page and recognize text by OCR. OCR words shall have `extraction_method == "ocr"`, an OCR-derived confidence, and all word attributes the OCR engine can supply; attributes it cannot supply (e.g., font name, glyph codes) shall be null. The page-level `extraction_method` shall be `"ocr"`.
AC: Given TestCase1.pdf, When extracted, Then `extraction_method == "digital"`.
AC: Given c4.pdf (no text layer; text drawn as 98 raster images), When extracted, Then `extraction_method == "ocr"` and `word_count > 0`.
AC: Given c4.pdf, When extracted, Then a word with `text == "xxxxxxx0178"` exists with `extraction_method == "ocr"` and `font == null`.

**FR-OCR-002 — OCR alongside other primitives**
OCR adds words; it does not replace or remove anything drawn on the page. On an OCR page, images and paths are still reported per FR-IMAGE-001 and FR-PATH-001, even where OCR words overlap them (BR-003).

What OCR reports depends on what it could resolve:
- **Characters read.** A word with its text, its box, and the engine's confidence.
- **A text region found, but no characters the system is willing to stand behind** (recognition confidence below the reporting floor, DD-7): a word with an empty `text`, its box, and that confidence. The region is known to hold something; its value is not.
- **A mark that cannot be resolved to text at all** (an icon, a logo, a smudge): nothing. It is not reported as a word. Whatever drew it is already reported as an image or a path, so nothing on the page is lost.

A junk string is never reported as if it were text: the system does not guess (BR-004). An empty value is still a value, so such a word is scored (§2) — at a confidence that will fail any useful threshold.
AC: Given c4.pdf, When extracted, Then no word's `text` is a junk string recognized from an icon; such regions are either absent or present with `text == ""` and a low confidence.
AC: Given c4.pdf, When extracted, Then every word with `text == ""` has a confidence below the reporting floor and a bbox.

**FR-OCR-003 — OCR word location**
Every OCR word shall have a bbox in page coordinates (§2), mapped from the rendered image to the page. The word's location is independent of whatever image or vector content it was recognized from.
AC: Given c4.pdf, When extracted, Then the word `"xxxxxxx0178"` has a bbox within 2 pt of `{x0: 439, top: 278, x1: 497, bottom: 286}`.

**FR-FORM-001 — Form controls**
The system shall report every form control (AcroForm widget) on the page with its location, type, name, and value (§5.1). Nothing the control draws for itself — its box, border, checkmark, or displayed text — shall be reported as words or paths; the control is reported once, as a control. This is a deliberate exception to BR-003.
Rationale: someone rebuilding the form needs to know a control exists at that location so they can ask for its code (which a person provides); a consumer that wants only the data reads `value` and ignores the control.
Anything the page itself draws around or beneath a control (for example, a printed checkbox square in the page content) is page content and is reported normally.
A field with several widgets (e.g., a group of checkboxes sharing one field name) is reported as one control per widget, each with its declared name.
A page with no form, or with a flattened form, reports `form_control_count == 0`; on a flattened form, the former values are ordinary page content and are reported as words.
AC: Given TestCase1.pdf, When extracted, Then `form_control_count == 0`.
AC: Given fw9.pdf (6 pages; page 1 has an empty fillable form), When extracted, Then `form_control_count == 23`, of which 15 are `text` and 8 are `checkbox`.
AC: Given fw9.pdf, When extracted, Then a `text` control exists with `name == "topmostSubform[0].Page1[0].f1_01[0]"`, `value == ""`, and bbox `{58.6, 118.0, 576.0, 132.0}`.
AC: Given fw9.pdf, When extracted, Then a `checkbox` control exists at `{73.0, 180.2, 81.0, 188.2}` with `value == "Off"`, and a rectangle path from the page content also exists at the same bbox.
AC: Given fw9.pdf, When extracted, Then no control has `control_type == "signature"` (the "Signature of U.S. person" area is a drawn line and words, not a control).
AC: Given fw9_filled.pdf, When extracted, Then `form_control_count == 23`; the control named `…f1_01[0]` has `value == "PAT Q SAMPLE"`; the checkbox at `{73.0, 180.2, 81.0, 188.2}` has `value == "1"`; the other seven checkboxes have `value == "Off"`; and the control named `…f1_09[0]` has `value == "ACME TEST CO\n1 EXAMPLE PLAZA\nCHICAGO, IL 60601"`.
AC: Given fw9_filled.pdf, When extracted, Then no word has text `"SAMPLE"` or `"TEST-0001"` (displayed values are not reported as words).
AC: Given fw9_filled_flattened.pdf, When extracted, Then `form_control_count == 0` and words `"PAT"`, `"Q"`, `"SAMPLE"` exist with top ≈ 120.6 and font `"Helvetica"`.
AC: Given fw9_filled_flattened.pdf, When extracted, Then nine words with text `"0"` exist at top ≈ 379.6 (a comb field draws each character in its own cell, so each digit is its own word).
AC: Given fw9_filled_flattened.pdf, When extracted, Then a word with font `"ZapfDingbats"` and glyph code `0x33` exists at x0 ≈ 74.8, top ≈ 178.6. (This is the flattened checkmark. It is reported as-is under FR-TEXT-002; recognizing it as a checkmark is the Structure skill's job.)

**FR-ANNOT-001 — Annotations excluded**
The system shall not report annotations of any kind, and shall not report anything an annotation draws for itself as words or paths. Annotations (comments, text-box comments, stamps, links, markup, ink, and the rest) are added to a PDF after the document was produced; DocExtractor reports the document, not what was added to it (OOS-007). What the page itself draws is reported normally, including a highlight that is part of the page content, and the words a link covers.
AC: Given annotations.pdf, When extracted, Then no word has text `"APPROVED"` (the stamp) and no word contains `"Confirm this list with the business owner."` or `"Test comment: check the tax-waiver wording."` (the comments).
AC: Given annotations.pdf, When extracted, Then no path exists at the ink drawing ≈ `{73, 683, 207, 712}` and none at the reviewer highlight ≈ `{101.6, 136.3, 250.8, 148.2}`.
AC: Given annotations.pdf, When extracted, Then exactly one yellow filled path exists, at ≈ `{104.4, 192.2, 270.9, 204.1}` (the original-document highlight), with a lower paint order than the word `"Photocopies"` it sits behind.
AC: Given annotations.pdf, When extracted, Then words `"Account"` and `"Application"` exist at the link location ≈ `{104.4, 164.2, 196.7, 176.1}`.
Caveat: an annotation that has been flattened into the page is page content and cannot be told apart from the original (OOS-008).
Implementation caution: some PDF libraries include annotation appearances in their list of page drawings (PyMuPDF's `get_drawings()` does). Those must be excluded.

**FR-CONF-001 — Confidence**
Digital words shall have confidence 1.0, or 0.0 when `unmapped_glyphs` is true. OCR words shall have the OCR engine's confidence normalized to [0.0, 1.0]. Every form control shall have confidence 1.0, whether or not its value is empty (the value is read, not recognized). Paths, images, and barcode regions shall have confidence null.
AC: Given TestCase1.pdf and threshold 0.9, When extracted, Then `scored_count == word_count`, `count_at_threshold == word_count`, and `overall_confidence == word_count`.
AC: Given fw9.pdf (empty form), When extracted, Then `scored_count == word_count + 23` (every control is scored, including empty text boxes and unchecked checkboxes).
AC: Given fw9_filled.pdf, When extracted, Then `scored_count == word_count + 23`.
AC: Given any test PDF and no threshold argument, When extracted, Then `count_at_threshold == scored_count`.
AC: Given c4.pdf and threshold 0.8, When extracted, Then `0 < count_at_threshold < scored_count` (regions OCR could not read produce empty values at low confidence).
AC: Given any test PDF, When extracted, Then `overall_confidence` equals the sum of the `confidence` values of all primitives whose confidence is not null.

**FR-SUMMARY-001 — Summary**
The system shall report primitive counts by kind, the scored count, the count at threshold, and the overall confidence (a sum, per §2).

**FR-DIAG-001 — Warnings**
The system shall report non-fatal conditions that affect extraction quality as warnings rather than failures, including at minimum: glyphs with no Unicode mapping, OCR invoked, and OCR text discarded below the reporting floor (FR-OCR-002).

# 7. Non-functional Requirements

**NFR-1 — Performance**
No requirements.

**NFR-2 — Scalability / Isolation**
Each invocation is stateless and fully isolated: no shared global state, no fixed temporary file paths, no reliance on files left by another invocation. The Consuming Application must be able to run multiple instances concurrently.
AC: Given the Consuming Application runs N concurrent invocations on different test PDFs, When each completes, Then each output is identical to that PDF's output from a solo invocation.

**NFR-3 — Environment**
Python 3 (minimum version: design). Runs locally.

**NFR-4 — Determinism**
Given the same input and threshold, and the same OCR engine version and configuration, the system shall return identical output.
AC: Given any test PDF, When extracted twice, Then the two outputs are byte-identical.

**NFR-5 — Language**
American English is the only supported language. Content in any other language is extracted on a best-effort basis with no guarantee of correctness: the system returns whatever it extracts and never deliberately drops it (BR-003). Non-text primitives (paths, images, page geometry) are unaffected by language.
AC: Given a digital PDF in American English, When extracted, Then every glyph is returned with its correct Unicode value.
Note (no AC — best effort): on digital pages, text is taken from the PDF's own Unicode mapping, so Spanish or Russian text will usually come through intact. On OCR pages, recognition uses an English model, so Spanish will be partly recognizable and Cyrillic will produce low-confidence or meaningless words.

**NFR-6 — Security**
See LIM-001.

**NFR-7 — Privacy**
See LIM-001.

**NFR-8 — Reliability**
No stated requirements.

**NFR-9 — Error handling**
For input meeting IF-002, the system never fails; it returns whatever it extracted. A page with nothing on it returns empty `primitives` and zero counts. Conditions that degrade quality are reported per FR-DIAG-001.

**NFR-10 — Observability**
No stated requirements beyond FR-DIAG-001.

**NFR-11 — Portability**
Not required.

**NFR-12 — Maintainability**
No stated requirements.

**NFR-13 — Consumability by an LLM**
Output is consumed by an LLM, so its size is a design constraint: text is reported at word granularity (not per glyph), and keys are self-describing. Target: the output for TestCase1.pdf should be small enough to read in a single model turn (budget: DD-3).

# 8. Business Rules

**BR-001 — Contains, never means**
DocExtractor shall not identify or label paragraphs, lines of text, lists, list markers, drawn checkboxes or their state (declared form controls are reported under FR-FORM-001), tables, cells, rules, borders, margins, backgrounds, headers, logos, or invisible/printer content. These are the Structure skill's conclusions.

**BR-002 — Barcodes are located, never decoded**
DocExtractor shall not decode barcode content or identify barcode symbology.

**BR-003 — Nothing dropped, nothing merged**
DocExtractor shall not filter, deduplicate, or combine primitives. Exceptions: nothing a form control draws for itself is reported, the control being reported once (FR-FORM-001); and annotations, with everything they draw, are not reported at all (FR-ANNOT-001).

**BR-004 — Never guess** (inherited from `specScan` Rule 0)
When DocExtractor cannot determine an attribute, it reports null and, where relevant, a warning. It never substitutes a plausible value.

# 9. Non-Goals / Out of Scope

**OOS-001** — Deriving document structure (Structure skill).
**OOS-002** — Barcode decoding and symbology identification.
**OOS-003** — Input validation (IF-002).
**OOS-004** — Pages other than the first.
**OOS-005** — OCR of text inside raster images on a page that has a text layer. Such images are reported as images (FR-IMAGE-001) and nothing more. Example: the "CREAM Ale" title in TestCase4.pdf is part of a raster image and will not appear as words.
**OOS-006** — Accepting a data contract from a consumer. Shaping or filtering output to what a consumer asks for is the calling skill's responsibility; DocExtractor's output is always complete and fixed.
**OOS-007** — Annotations of every kind: comments, text-box comments, stamps, links, markup (highlight, underline, strikeout, squiggly), ink, file attachments, sound, video, and the rest. They are added after the document was produced, so they are not part of what the page draws (FR-ANNOT-001). The words a link covers are reported as words in the normal way.
**OOS-008** — Telling a flattened annotation from original content. Once a reviewed PDF is flattened, an added highlight becomes page content and is reported as a path like any other.
**OOS-009** — *(retired in v0.9; folded into OOS-007.)*
**OOS-010** — XFA form definitions (excluded for now). Only AcroForm widgets are reported. A form defined only in XFA (a "dynamic XFA" PDF) reports its printed page but no form controls. (fw9.pdf carries both XFA and AcroForm; its AcroForm widgets are reported.)

# 10. Limits / Constraints

**LIM-001 — No exfiltration**
All processing is local. DocExtractor makes no network connections and uses no remote services (including cloud OCR).

**LIM-002 — Single page per call**
One call extracts one page.

# 11. Product Success Metrics

**SCS-001** — All acceptance criteria in §6 pass against the test corpus.
**SCS-002** — The Structure skill, given only DocExtractor output, reproduces each WorkedExample JSON within 0.02 in on every location and size. Style values are excluded: WorkedExample1.json predates recent fixes and its styles are known to be wrong.
**SCS-003** — On c4.pdf, OCR recognizes the printer mark `"JAN005237179"` (drawn about 3 pt tall at top left). Stretch goal, not an AC: in a trial, Tesseract read it correctly at 300 dpi but at a confidence of only 0.52, and misread it at 600 dpi.

# 12. Deferred Decisions (design)

**DD-1** — Exact output key names.
**DD-2** — Rotation convention (clockwise vs. counter-clockwise; 90 vs. 270 for bottom-to-top text).
**DD-3** — Output size budget for NFR-13.
**DD-4** — PDF parsing library, OCR engine, barcode detector (all must satisfy LIM-001).
**DD-5** — Word-splitting rule for tight kerning and inter-glyph gaps.
**DD-6** — OCR render resolution. Trial on c4.pdf page 1 with Tesseract 5.3.4: 300 dpi gave 316 words, mean confidence 89; 600 dpi gave 303 words, mean confidence 91 but more misreads. Higher is not automatically better.

**DD-7** — The OCR reporting floor: the recognition confidence below which recognized characters are not reported, leaving an empty value (FR-OCR-002). Needs tuning against c4.pdf, where the printer mark reads at about 0.52 (SCS-003) and must not be discarded.

# 13. Open Questions

- **OQ-1** — *Resolved v0.3:* non-English is best effort, nothing dropped (NFR-5).
- **OQ-2** — *Resolved v0.4:* data contracts belong to the calling skill (OOS-006).
- **OQ-3** — *Resolved v0.4:* one entry per word. Whitespace is not a word; gaps between words are recoverable from bboxes.
- **OQ-4** — *Resolved v0.4:* images on digital pages are not OCR'd (OOS-005).
- **OQ-5** — *Resolved v0.4:* form controls are in scope (FR-FORM-001).
- **OQ-5a** — *Resolved v0.5:* the value is reported on the control only (FR-FORM-001).
- **OQ-5b** — *Resolved v0.5:* comments and stamps in scope; links and markup out. *Superseded v0.9:* no annotations are reported at all (FR-ANNOT-001, OOS-007).
- **OQ-5c** — *Resolved v0.6:* nothing a control draws for itself is reported; the control carries location, type, and value (FR-FORM-001).
- **OQ-5d** — *Resolved v0.6:* out of scope (OOS-009).
- **OQ-6** — *Resolved v0.5:* no; only location is reported.
- **OQ-7** — *Resolved v0.5:* overall confidence is the sum; count uses ≥.
- **OQ-7a** — *Resolved v0.6:* barcode regions are not scored; they carry `detection_confidence` instead.
- **OQ-7b** — *Resolved v0.7:* form control values are scored at 1.0 when not empty, because they are read, not recognized.
- **OQ-7c** — *Resolved v0.8:* "not checked" and "empty" are values; every control is scored.
- **OQ-14** — *Resolved v0.8:* XFA is excluded for now (OOS-010).
- **OQ-8** — *Resolved v0.5:* bytes in, bytes out (IF-001).
- **OQ-8a** — *Resolved v0.6:* default 0.0.
- **OQ-9** — *Resolved v0.3:* WorkedExample1.json is authoritative for position only; its styles are stale (actual font is DejaVuSans 8 pt). Regenerate it, or keep SCS-002's style exclusion.
- **OQ-10** — *Resolved v0.8:* the product is named DocExtractor.
- **OQ-11** — *Resolved v0.7:* test corpus completed (§5.2). A hybrid page (text layer plus a raster image containing text) is covered by TestCase4.pdf.
- **OQ-12** — *Resolved v0.4:* OCR words need page location only, not a link to image fragments (FR-OCR-003).
- **OQ-13** — *Resolved v0.8:* c4.pdf is the AFP-to-PDF case.
