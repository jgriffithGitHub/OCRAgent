import os
import gc
import json
import httpx
import re
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from datetime import datetime
#------------------
from PIL import Image
import numpy as np
import cv2


# Force the underlying Paddle framework to see 0 GPUs before initializing.
# This keeps the OCR execution bound to your CPU, leaving your VRAM pure for Ornith!
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Correct parameters matching the modern PaddleOCR API structure
# enable_mkldnn=False works around a PaddlePaddle 3.3.1 framework bug (fixed on
# develop, not yet released to PyPI as of paddlepaddle 3.3.1 / paddleocr 3.7.0):
# the default oneDNN CPU acceleration path can't convert a particular attribute
# type in the text-detection model's PIR graph and raises NotImplementedError
# (ConvertPirAttribute2RuntimeAttribute ... pir::ArrayAttribute<pir::DoubleAttribute>).
# Turning oneDNN off routes inference through the plain (slower but correct) CPU
# kernels instead. See https://github.com/PaddlePaddle/PaddleOCR/issues/18162 and
# https://github.com/PaddlePaddle/Paddle/issues/77340.
ocr = PaddleOCR(use_textline_orientation=True, lang='en', enable_mkldnn=False)

# Local Ollama model used to interpret the OCR coordinate map into structure.
# Swapped from ornith:9b (a 9B model that couldn't finish a single page inside
# the 120s timeout below, on this CPU) to qwen3:4b, which is far smaller and
# should comfortably fit the time budget for this fairly light classification/
# labeling task -- PaddleOCR has already done the hard perceptual work by the
# time this model sees anything.
LLM_MODEL = "qwen3:4b"

# Target structure schema matching your desired template breakdown
PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "page_style": {"type": "string", "enum": ["form", "table_grid", "raw_text", "blank"]},
        "detected_anchors": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List unique structural keys found on this page (e.g., 'Invoice Number', 'Plate State')"
        }
    },
    "required": ["page_style", "detected_anchors"]
}

def process_single_page_ocr(pil_image):
    """Extract coordinates on CPU and heavily strip out content values to save context RAM."""
    width, height = pil_image.size

    # PaddleOCR's ocr()/predict() only accepts a file path (str) or a numpy array in
    # BGR order (the same convention cv2.imread uses) -- it never accepts a PIL Image
    # object. Passing pil_image straight in was silently rejected ("Not supported
    # input data type!" in test_run.log) and the page was skipped entirely, which is
    # why every page came back with an empty coordinate map.
    bgr_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    raw_result = ocr.ocr(bgr_array)

    ocr_lines = []
    # PaddleOCR 3.x's ocr()/predict() returns a list of dict-like OCRResult objects
    # (one per page), each holding parallel "rec_polys" (a quad box per detected text
    # line) and "rec_texts" (the recognized string per line) lists. That is a
    # different shape from the deprecated PaddleOCR 2.x [[box, (text, score)], ...]
    # structure the old loop below assumed, so it has to be unpacked differently.
    if raw_result and raw_result[0]:
        page_result = raw_result[0]
        for bbox, text in zip(page_result["rec_polys"], page_result["rec_texts"]):
            text = text.strip()  # Clean raw string

            # --- RAPID REGEX FILTER ---
            # If text is purely a number, dollar amount, date, or code value, skip it!
            # This isolates purely physical text structural anchor labels.
            if re.match(r'^\$?[\d.,\-/\\:]+$', text) or len(text) <= 2:
                continue

            # Compress positions onto a standard 0-1000 grid map
            top = int((min(p[1] for p in bbox) / height) * 1000)
            left = int((min(p[0] for p in bbox) / width) * 1000)
            ocr_lines.append(f"[{top},{left}]->\"{text}\"")

    return "\n".join(ocr_lines)

def analyze_page_with_ornith(client, ocr_text):
    """Synchronous single-page call to the local Ollama model (see LLM_MODEL), sized for 4GB VRAM / 16GB RAM."""
    prompt = (
        f"Analyze the physical coordinate map below. Coordinates are [Top, Left] on a 1000x1000 canvas.\n"
        f"Identify structural anchors and field labels that define this page layout:\n\n{ocr_text}"
    )
    try:
        response = client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,  # skip qwen3's internal reasoning trace -- go straight to the answer
                "format": PAGE_SCHEMA,
                "options": {
                    "num_ctx": 8192,     # Limit context canvas to protect shared system RAM
                    "temperature": 0.0,   # Keep extraction deterministic 
                    "num_predict": 1024   # Limit max tokens generated
                }
            },
            timeout=120.0 # High timeout because CPU/RAM swapping slows processing down
        )
        return json.loads(response.json()["message"]["content"])
    except Exception as e:
        return {"error": str(e), "page_style": "failed", "detected_anchors": []}

def grind_documents(pdf_folder):
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    print(f"Beginning offline processing of {len(pdf_files)} files using {LLM_MODEL}...")
    
    with httpx.Client() as client:
        for file in pdf_files:
            pdf_path = os.path.join(pdf_folder, file)
            print(f"{datetime.now()}  Processing document: {pdf_path}")
            
            # Lower DPI to 150 to heavily minimize RAM consumption during rasterization
            pages = convert_from_path(pdf_path, dpi=150)
            document_structure = {}
            
            for idx, page_img in enumerate(pages):
                # 1. Run CPU OCR
                ocr_text = process_single_page_ocr(page_img)
                
                # 2. Extract layout template structure
                page_data = analyze_page_with_ornith(client, ocr_text)
                document_structure[f"page_{idx+1}"] = page_data
                print(f"{datetime.now()}  Processed Page {idx+1}/{len(pages)}")
                
                # 3. Aggressive RAM purging after every single page loop
                del ocr_text
                gc.collect()
                
            # Save progress incrementally so you never lose data if the system swaps too hard
            with open(f".\\outputs\\structure_{file}.json", "w") as f:
                json.dump(document_structure, f, indent=2)
            
            # Clear file images out of system memory
            del pages
            gc.collect()

if __name__ == "__main__":
    # Ensure this directory exists and contains your PDFs
    TARGET_FOLDER = ".\\pdf_inputs" 
    grind_documents(TARGET_FOLDER)
