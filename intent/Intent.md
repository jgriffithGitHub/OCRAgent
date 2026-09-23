# Project Name

OCRAgent

## Problem Statement

Documents provide a "human-level" way to transfer information, but encoding data as characters printed on paper is difficult for machines to understand. The first level of the problem is extracting individual characters. The rest of the problem is extracting meaning from the characters, and that meaning is derived largely from their physical position. Characters that are physically next to each other become words, and collections of words become lines, paragraphs, lists, and tables. The overall structure of the document and the location of those blocks on the page also carry meaning: a "letter" has a specific format and, within that format, a group of lines near a corner of the page is often an address block that shows through an envelope window, while a few lines below a closing tell the reader who sent it.

So, to use documents as a data-transfer medium, three problems must be solved:

1. Find everything the page contains: every character, line, shape, image, and barcode, and where each one is.

2. Combine those contents into meaningful layout: paragraphs, lists, tables, rules, margins.

3. Decide which parts of the document carry data, and where that data comes from.

This project solves problems 1 and 2 automatically, and supports a person in solving problem 3. It deliberately keeps them apart, because each has a different kind of certainty. What a page *contains* can be read with near-certainty from a digital PDF. What the contents *mean* as layout is a judgment. What the data *is* needs business context that only a person (or, in future, a system with that context) has.

The project will not infer what type of document it is looking at. A few document types (a letter, a claim, a statement) have recognizable structures, but many do not. A consuming application often has context this project does not (for example, a claims process that only produces three types of documents) and can make that call from the layout this project provides.

### Knowing what it does not know

The ability to recognize characters depends on the fidelity of the document and its typography. If the text can be read directly from the digital format (the text layer of a PDF), the project can be confident it is correct. If the characters must be recognized from their shapes in an image (OCR), it cannot. Some PDFs have no text layer at all: PDFs converted from AFP print streams, for example, contain each line of text as a separate raster image.

How much confidence is enough depends on the consumer. If an application scanning a bank statement already has the account data from another source, 100% confidence on the account number and the statement date may be all it needs. An application reading a medical history may need 95% confidence on every value. An application that only wants the layout of a letter may not care about the values at all.

This project does not know which of these situations it is in, and an agentic consumer may adapt its processing to the confidence it is given. So the project reports confidence rather than deciding on the consumer's behalf. For every value it reads, it returns a confidence score. The consumer supplies one minimum acceptable confidence (a threshold), and the project returns:

- the confidence score of every value it read;
- the number of values whose confidence meets the threshold;
- the overall confidence: the sum of all value confidence scores;
- how the page was read: digitally from the text layer, or by OCR.

The overall confidence alone is a "low bar". Suppose a consumer expects 10 values and will accept the result if each has at least 85% confidence, i.e. an overall confidence above 8.5. If the project reads nine values at 100% and misses the tenth entirely, the overall confidence is 9.0, above the bar, but the result is not acceptable. The count of values that meet the threshold (nine) shows that immediately. And if the consumer sets a threshold of 50% and one value is read at 30%, that value is still returned with its score but is not counted.

Other statistics were considered, such as the average confidence. The project stops one mathematical step short of that by returning the raw sum and the counts. The average adds little that the components do not already give, and a consumer that wants it (or a standard deviation) can compute it from the per-value scores.

## Core Capabilities

The project provides one tool and two skills. Each skill builds on the one before it. The two skills replace the DocSpec skills `specScan` and `specReview`: watching Claude run them showed that the measuring part of `specScan` could be done more reliably by a tool, so that part became DocExtractor, and the skills keep their output formats.

### DocExtractor (tool)

Reports what a single PDF page contains: every word, vector path (lines, rectangles, curves), raster image, barcode region, and form control, with position, size, style, and drawing order. It reports everything, including hidden, overlapping, rotated, and duplicate content, and never decides what anything means. It locates barcodes but never decodes them.

- When the page has a text layer, its text is read digitally. When it has none, the text is read by OCR. One method is used for all the text on a page, never mixed. (Shapes and images are always read from the PDF itself.)
- Values (words and form-control values) carry a confidence score. Shapes, images, and barcodes are located but carry no value, so they are not scored.
- It extracts the first page of the PDF it is given and reports how many pages the PDF has. Splitting a document into pages is the caller's job, which keeps the tool simple and avoids passing a 600-page PDF in one call.
- It is hosted by a consuming application or a skill; it is not a standalone program.

Specification: `DocExtractor_PRS.md`.

### Structure skill

Turns DocExtractor's inventory into a layout specification of the whole document: for each page, the margins, the page background, and an ordered list of paragraphs, list items, tables (as rows of cells), rules, images, and barcodes, with their locations, sizes, and styles. Content a reader cannot see (invisible text, printer marks) is reported as ordinary paragraphs with its true color and size, never dropped. Anything it cannot recognize, it says so, with the location. The output is the `specScan` JSON format from the DocSpec project, and it takes every measurement from DocExtractor rather than measuring the page itself.

Specification: `Structure_PRS.md`.

### Mapping skill

Supports a person in reviewing what a document's content depends on. From the PDF and its Structure output, it draws a numbered box around every leaf item (each paragraph, list item, image, barcode, rule, and every individual table cell) and produces a workbook with one row per box. The skill fills in each item's number, page, and content; the person records whether the item is conditional and whether it comes from external data. Between them the two artifacts tell the analyst what has to be worked out and give them a checklist for doing it. The path runs one way — from the document to the marked-up copy and the first version of the workbook — and never back.

Specification: `Mapping_PRS.md`.

## Constraints

- The project never infers the type of a document.
- DocExtractor reports what the page contains and never what it means. All layout conclusions are made in the Structure skill.
- The Structure skill describes layout only. A group of lines at the top of a page is reported as a paragraph, not as an address, because the project cannot be certain of its purpose.
- The Mapping skill never decides which items are conditional or data; a person does.
- The process always runs in order: extraction (DocExtractor), then structure, then mapping. The Mapping skill never runs alone.
- Confidence applies only to values that were read, not to positions.
- One method (digital or OCR) for all the text on a page, never mixed.
- Nothing is guessed. What cannot be determined is reported as unknown, with a warning, never replaced by a plausible value.
- Every result belongs to one specific PDF. If the PDF changes, new results are produced and the analyst's work is moved across by hand. For the same PDF, each run of a skill and each correction by an analyst creates a new numbered version; earlier versions are kept, and any two versions can be compared to see what changed (for example, when judgment grouped the content differently).

## Primary users

- **Document analysts** who need to rebuild existing documents in a document-generation system and need an accurate layout specification (Structure skill) and a record of where each item's data comes from (Mapping skill).
- **Consuming applications and agents** that need page contents with reliable confidence information. How they use it is not known: they may be building document specifications, extracting key values to look up other information for a customer-service task, or summarizing a document and presenting the extracted values alongside the summary.
- **Data owners and developers** who build the data feeds that supply documents and need the completed mapping workbook.

## Performance

There is no performance requirement. Earlier testing suggests some single pages (for example, AFP converted to PDF, read by OCR) may take up to a minute, depending on the document and the hardware.

## Security

The project provides capabilities on which other services are built, so authentication and authorization are the responsibility of the consuming application.

The project must not leak document content. All processing is local; the tool makes no network connections and uses no remote services, including cloud OCR. This is a technology-selection criterion: a prototype built with PaddleOCR and an Ollama-hosted model showed that both can connect to the Internet and might pass data to their hosts. (Whether the same rule applies to the model that runs the skills is an open question; see Structure_PRS.md OQ-12.)

DocExtractor retains nothing between calls. The skills' outputs are files that contain document content (the structure specification, the raw extraction it was built from, the annotated PDF, and the workbook); they are written only beside the input PDF or where the caller directs, and are kept as numbered versions. The data resides with the PDFs: these files carry the same sensitivity as the PDF they describe, and the end user is responsible for making sure that any PII in them, as in the PDF itself, is not exposed.

The project does not know where its input came from or what it contains, so handling of Personally Identifiable Information (PII) is the consuming application's responsibility.

## Other Non-functional Requirements (NFRs)

- American English is the supported language. Other languages are extracted on a best-effort basis; content is never deliberately dropped.
- Each call is independent, so a consumer can run several at once.
- Given the same input (and the same OCR engine version), DocExtractor returns identical output.

No other non-functional requirements are known at this time.

## Out of Scope

The following are out of scope for this version:

- **Identifying variable data (the Dynamic Data skill).** Suggesting or deciding which content is variable data, and finding where that data comes from, is a separate, future project. Today a person does this after the Mapping skill runs: keeping the workbook on the right row and the PDF in view while working with a DBA, database tools, and data catalogs. The Dynamic Data project exists to reduce that tedious work.
- Connecting to data sources, or turning a completed mapping workbook into a query or data contract.
- Tools that compare versions, or that carry an analyst's work from one version or one PDF to another. This version only keeps versions and makes them comparable. The same applies when a document changes enough that its artifacts are superseded: transferring what still applies, and identifying what has to be gathered again, needs a tool this project does not include.
- Turning the completed artifacts into a report. Once the workbook is filled in, it and the marked-up copy describe what the document is and where its data comes from; that eventually has to become a readable account of what the software does, so that nobody has to read the code to find out. Producing it is outside this project.
- Generation requirements: the rules a document must follow when it is rebuilt. They come in layers — corporate (branding, accessibility), department (statement producers minimizing sheet count while marketing adds offers on separate sheets), and document — and a PDF records none of them; it shows one outcome of them. Keeping a group of rows together on a page is one such rule: the project can report that a row split across pages, not that the rule existed. The analyst supplies these.
- Inferring document type, or the business meaning of any content.
- Decoding barcodes.
- OCR of text inside images on pages that do have a text layer.
- Accepting a record structure or data contract from a consumer and returning data in that shape. Shaping the output is the calling skill's responsibility; DocExtractor's output is always complete and fixed.
- Per-value thresholds; one threshold applies to every value.
- Annotations of every kind (comments, stamps, links, highlights, ink and the rest). They are added to a PDF after the document was produced, so they are not part of the document being described; the words a link covers are still reported. XFA-only forms.

## Success Criteria

The project must know what it does not know. DocExtractor meets this by returning a confidence score for every value it reads, the number of values that meet the consumer's threshold, the overall confidence, and the reading method (digital or OCR), for everything on the page, with nothing dropped and nothing interpreted.

The Structure skill succeeds when, given only DocExtractor output, it reproduces the layout of the worked examples (locations and sizes within 0.02 inch).

The Mapping skill succeeds when every item on the document has a numbered box in the right place and a matching workbook row, so that a person can review every item without having to find or box any by hand.
