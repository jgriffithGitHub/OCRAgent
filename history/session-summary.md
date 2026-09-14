# OCR Agent — Origin & Context Summary

Written to seed a new Claude project. This captures how this codebase got here, what's been proven, what's been decided, and what's still open — so a fresh session (or a new project) doesn't have to reconstruct it from scratch.

## Where this came from

`testAgent.py` started as a debugging exercise inside a different project (DocSpec, which owns a `specScan` skill for reverse-engineering PDF layouts into a structured JSON spec). The idea was: DocSpec's `specScan` process can't handle PDFs converted from AFP composition, because those have no real text layer — every line of text is a separately rasterized bitmap image. `testAgent.py` was a prototype for a fully local, offline pipeline (PaddleOCR for text extraction, a local Ollama model for interpreting the result) to see whether OCR + a local LLM could make sense of that kind of document at all.

That investigation is now closed on the DocSpec side — worth knowing so this project doesn't accidentally re-litigate it:

- `specScan`'s actual process (documented in `skills/specScan/SKILL.md`) already handles AFP-converted PDFs, just not via OCR. It pulls exact bounding boxes for each rasterized text line directly from the PDF's embedded image XObjects (via `pdfplumber`), and reads the actual text content **visually**, from labeled contact-sheet mosaics of the bitmaps — deliberately not trusting OCR for content, because plain Tesseract got a meaningful fraction of numeric values wrong (digit transpositions, `$`→`S`/`§` confusion) when it was tried.
- That approach already produced a complete `c4.json` for the same test document (`JanusSamples/c4.pdf`, a 6-page Janus Henderson confirmation statement) used throughout this debugging session — so `specScan` doesn't need `testAgent.py` as a fallback tool. (That `c4.json` hasn't had the same second independent review pass that other worked examples got, but that's a thoroughness gap, not a capability gap.)
- Conclusion: `testAgent.py` is not going back into DocSpec. It's being spun out here as its own thing.

## What testAgent.py actually does (as of this session)

Pipeline: render each PDF page to an image (`pdf2image`) → run PaddleOCR on it to get coordinate-tagged text lines → filter out purely numeric/date/currency lines with a regex (keeping only label-like text) → hand the remaining text, as a coordinate map, to a local Ollama model → ask it (via a JSON-schema-constrained call) to classify the page's `page_style` and list `detected_anchors` (structural field labels).

## Bugs found and fixed this session (in order)

1. **Wrong input type to PaddleOCR.** The code called `ocr.ocr(pil_image)` with a raw PIL Image. The installed `paddleocr==3.7.0`'s reader only accepts a file path (`str`) or a `numpy.ndarray` in BGR order — a PIL Image is silently rejected (logged as `Not supported input data type!`), so every page's OCR silently returned nothing. Confirmed by reading the actual installed library source (`paddlex/inference/common/reader/image_reader.py`), not by assumption.
   - **Fix:** convert the PIL image to a BGR numpy array first: `cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)`.

2. **Result-parsing code written for the wrong PaddleOCR API version.** Even with valid input, the old loop (`for line in raw_result[0]: bbox = line[0]; text = line[1][0]`) assumed the deprecated PaddleOCR 2.x return shape (`[[box, (text, score)], ...]`). The installed 3.7.0 actually returns a list of dict-like `OCRResult` objects per page, keyed `rec_polys` (box per line), `rec_texts` (string per line), and `rec_scores` (confidence per line) — confirmed in `paddlex/inference/pipelines/ocr/pipeline.py`.
   - **Fix:** unpack via `zip(page_result["rec_polys"], page_result["rec_texts"])`.
   - **Note carried forward:** `rec_scores` exists and is currently still being discarded. This turned out to matter later (see "Where this is headed," below).

3. **Upstream PaddlePaddle framework bug**, not a bug in this code: `paddlepaddle==3.3.1`'s default oneDNN/CPU acceleration path, run through its newer PIR graph executor, can't convert one particular attribute type used by the text-detection model, and throws `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`. Confirmed as a known, exact-version-matched regression via [PaddleOCR issue #18162](https://github.com/PaddlePaddle/PaddleOCR/issues/18162) and [Paddle issue #77340](https://github.com/PaddlePaddle/Paddle/issues/77340) — a fix exists on Paddle's `develop` branch but hadn't shipped to PyPI as of 3.3.1.
   - **Workaround applied in code:** `enable_mkldnn=False` on the `PaddleOCR(...)` constructor (routes inference through slower but working plain CPU kernels).
   - **Actually resolved by:** downgrading the framework itself — `pip install paddlepaddle==3.2.2` (the last release before the regression), done directly by the user in his own terminal. This restores full oneDNN acceleration; the `enable_mkldnn=False` workaround in the code is now redundant (harmless to leave, but could be removed/reverted since the underlying bug is gone at 3.2.2).

4. **The LLM was too slow for its own timeout — not a crash, a silent failure mode.** With OCR actually working, `ornith:9b` (the original 9B model) consistently took longer than the hardcoded `httpx` `timeout=120.0` to generate even a short JSON response. The script's own `try/except` around the Ollama call caught every timeout and quietly recorded `{"page_style": "failed", "error": "timed out"}` for every single page in every file — the run "succeeded" (no traceback) while producing zero usable output. This was only caught by reading the actual output JSON, not by watching the terminal.
   - **Fix:** swapped the model to `qwen3:4b` (see below), which finishes comfortably inside the timeout.

## Model swap: ornith:9b → qwen3:4b

Reasoning: by the time the LLM sees anything, PaddleOCR has already done the hard perceptual work (finding and reading text). What's left is a lighter classification/labeling task over already-filtered, short input, using JSON-schema-constrained decoding (Ollama's `format` parameter) — a small model should hold up fine at that, and the per-page timing data supported it (pages were taking ~4 minutes each with the 9B model on CPU).

- Checked Ollama's actual model library (not blog SEO content, some of which was inventing nonexistent model names) to confirm real, current small-model tags: `qwen3` (0.6B/1.7B/4B/8B), `gemma3` (270M/1B/4B/12B), `llama3.2` (1B/3B), `phi4-mini` (3.8B).
- Picked `qwen3:4b`. One real gotcha: Qwen3 is a hybrid "thinking" model that by default emits an internal reasoning trace before answering (confirmed live — asking it "what model are you?" produced a visible `Thinking...` block). Ollama's `/api/chat` exposes a top-level `"think": false` flag specifically to skip this, which was added to the request.
- Code changes: pulled the model name into a named constant `LLM_MODEL = "qwen3:4b"` near the top of the file (so switching models later is a one-line change), updated the request body with `"think": False`, and fixed stale "Ornith" references in the startup print/docstrings.

**Result: it worked.** The run completed cleanly (no crash, no universal timeout), and — critically — produced genuinely different output per page instead of the old identical-every-page hallucination. `WorkedExample1.pdf` page 1 came back with specific, plausible field labels (`Invoice Number`, `Renter Name`, `Plate State`, etc.). `c4.pdf` pages 1, 4, and 5 also came back with real, page-specific content (fund names, `Account Number`, `Trade Date`, etc.).

**But a real quality gap surfaced on inspection**, worth carrying forward: `c4.pdf` pages 2, 3, and 6 came back with thin, generic anchors (`["Top", "Left"]`, `["top_left", "top_right", "bottom_left", "bottom_right"]`, `["top", "left"]`) — the same shape as the original all-hallucinated failure, just now isolated to specific pages. Diagnosis: those pages are dominated by numeric transaction data that the regex filter (correctly) strips out before it reaches the LLM, leaving it with an almost-empty coordinate map. Instead of saying "I see nothing here," the model falls back to inventing generic corner/direction labels. This is the seed of the whole next phase of the project (below).

**Side observation, unconfirmed:** GPU1 (an NVIDIA Quadro M1200) showed brief utilization spikes during LLM calls. Working theory: `CUDA_VISIBLE_DEVICES=""` in the script only scopes the Python/PaddleOCR process — Ollama runs as its own separate, already-running server process untouched by that variable, and likely auto-offloaded some of `qwen3:4b`'s layers to that GPU. Not verified directly; `ollama ps` while the script is actively mid-page would show a `PROCESSOR` column confirming this if it's worth knowing for certain.

## The pivot: from "specScan helper" to standalone portfolio project

Once the DocSpec integration idea was dropped (see above), the conversation turned to: this could be a genuine portfolio piece, given that meaningful AI-industry certifications are scarce (Claude Certified Architect exists but is partner-only) and hiring in this space leans heavily on demonstrable work. Explicit goal: build something with a real point of view, not just another OCR wrapper — "there are many of these out there (Microsoft has had one for years)."

**Competitive check before committing to a direction** (checked against Microsoft's own current documentation, not assumption): Azure AI Document Intelligence already ships per-cell/row/table confidence scores and some positional/bounding-box data — so "add confidence scores" or "report source position" are not real differentiators; that's already table stakes. Two things are notably *not* documented as built in anywhere in Azure's public docs:
1. Automatic grouping of related fields into a logical record (e.g., recognizing that a trade date, fund name, share count, and price all belong to one transaction line, rather than four unrelated key-value pairs).
2. Explicit "this is uncertain, I'm not going to guess" behavior when confidence is low — the docs are silent on whether the service ever declines to guess vs. always returning its best attempt.

That second gap is exactly the failure mode this session watched happen live (the `top_left`/`top_right` hallucination on sparse pages) — which makes it a credible, earned differentiator rather than a guess about what might be missing.

## Decisions made (via explicit discussion, not assumed)

- **Positioning:** this should showcase engineering judgment and rigor as the headline — not a narrow vertical pitch (e.g., not specifically "insurance document processing," even though that maps to the user's professional background).
- **Core differentiators, both confirmed important:**
  1. **Calibrated uncertainty** — the agent should be architecturally designed not to guess when it lacks signal, rather than being merely told not to via prompt instructions (which qwen3:4b just demonstrated it won't reliably honor on its own).
  2. **Relational record grouping** — flat extracted fields should be grouped into meaningful composite records (e.g., one transaction = fund + shares + price + date together), not handed back as isolated key-value pairs.

## Proposed architecture for the next phase (discussed, not yet built)

1. **Keep OCR extraction, but stop discarding `rec_scores`.** PaddleOCR already computes a per-line recognition-confidence score; the current code throws it away. This is a more trustworthy uncertainty signal than anything an LLM can self-report (LLM self-reported confidence is well known to be poorly calibrated).
2. **New deterministic stage: spatial grouping, no LLM involved.** Use the coordinate data already being computed (`rec_polys` top/left per line) to cluster OCR lines into row/column candidates via geometry alone — classic table-reconstruction-from-bounding-boxes. This does the "find the structure" work in code rather than asking the LLM to find structure in a flat wall of text from scratch.
3. **New deterministic gating stage.** Before ever calling the LLM, decide per-page (or per-group) whether there's enough OCR evidence density/confidence to proceed. If not, mark it `"insufficient_signal"` in Python and skip the LLM call entirely — don't rely on the model to notice its own input is thin.
4. **LLM stage narrows to semantic labeling only**, running only on pages/groups that pass the gate: given pre-grouped rows, identify what each group represents (this is a transaction line; here's its fund/shares/price/date) rather than discovering structure from scratch. The output schema itself should carry an explicit `"insufficient_data"`/abstain affordance rather than forcing every field to be filled.

**Open, not yet decided:** division of labor on building this. The user's stated preference (documented in his own working style) is to own conceptual/logic-writing himself — the row/column clustering geometry and the gating threshold logic are natural candidates for that — while scaffolding (OCR call plumbing, Ollama request/schema boilerplate) can be handed off. This was proposed at the end of the prior session but not yet confirmed or split up.

## Current file state (as of this handoff)

- `testAgent.py` in this folder reflects fixes 1–3 above and the `qwen3:4b` model swap (including `LLM_MODEL` constant and `"think": False`). It does **not** yet include the `rec_scores`-based gating, the spatial row/column clustering, or the record-grouping output schema — that's the next build phase.
- The `enable_mkldnn=False` workaround for bug #3 is still in the code but is likely no longer necessary now that `paddlepaddle` has been downgraded to 3.2.2 — worth revisiting/removing if the framework fix holds up.
- Old `structure_*.json` output files in this folder are a mix of pre-fix (hallucinated/timed-out) and post-fix (partially working) runs — worth regenerating cleanly once the next architecture phase lands, rather than treating any of the current ones as a baseline.
- Environment: Windows-native venv (`venv\Scripts\python.exe`, Python 3.13) with `paddleocr==3.7.0`, `paddlex==3.7.2`, `paddlepaddle==3.2.2`, `opencv-contrib-python==4.10.0.84`, `numpy==2.3.5`, `pillow==12.3.0`. Local Ollama server with `qwen3:4b` pulled (the only model currently installed — prior models were removed in a cleanup). Hardware: Intel HD Graphics 630 (integrated) + NVIDIA Quadro M1200 (discrete, ~4GB VRAM per the script's own comments) + 16GB system RAM, which ran close to full (up to 98%) during testing — worth keeping an eye on as the pipeline grows.
