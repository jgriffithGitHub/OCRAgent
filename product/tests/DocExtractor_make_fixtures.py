"""Rebuild the generated test fixtures for the DocExtractor spec (PRS §5.2).

Usage:  python make_fixtures.py <dir containing fw9.pdf and WorkedExample4.pdf>
Needs:  pymupdf, pypdf, reportlab, and LibreBarcode39-Regular.ttf in the same dir
        (https://github.com/google/fonts/tree/main/ofl/librebarcode39, OFL licence).
Writes: fw9_filled.pdf, fw9_filled_flattened.pdf, annotations.pdf, barcodes.pdf
"""
import sys, os
import pymupdf as fitz, pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.barcode import code39, qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

src = sys.argv[1] if len(sys.argv) > 1 else "."
here = os.path.dirname(os.path.abspath(__file__))

# --- fw9_filled.pdf: fictional values; XFA removed so every viewer shows the AcroForm values
VALUES = {"f1_01[0]": "PAT Q SAMPLE", "f1_07[0]": "123 TEST STREET APT 4",
          "f1_08[0]": "SPRINGFIELD, IL 62701", "f1_09[0]": "ACME TEST CO\n1 EXAMPLE PLAZA\nCHICAGO, IL 60601",
          "f1_10[0]": "TEST-0001", "f1_11[0]": "000", "f1_12[0]": "00", "f1_13[0]": "0000"}
d = fitz.open(os.path.join(src, "fw9.pdf"))
for w in d[0].widgets():
    short = w.field_name.split(".")[-1]
    if short in VALUES:
        w.field_value = VALUES[short]; w.update()
    elif short == "c1_1[0]":                      # Individual/sole proprietor
        w.field_value = w.on_state(); w.update()
d.save("/tmp/_fw9_filled.pdf", garbage=3, deflate=True)
wr = pypdf.PdfWriter(clone_from=pypdf.PdfReader("/tmp/_fw9_filled.pdf"))
wr._root_object["/AcroForm"].pop(pypdf.generic.NameObject("/XFA"), None)
wr.write(os.path.join(here, "fw9_filled.pdf"))

# --- fw9_filled_flattened.pdf
d = fitz.open(os.path.join(here, "fw9_filled.pdf")); d.bake()
d.save(os.path.join(here, "fw9_filled_flattened.pdf"), garbage=3, deflate=True)

# --- annotations.pdf
d = fitz.open(os.path.join(src, "WorkedExample4.pdf")); p = d[0]
find = lambda t: p.search_for(t)[0]
p.draw_rect(find("Photocopies of the death certificates"), color=None, fill=(1, 1, 0), overlay=False)  # original highlight
p.add_highlight_annot(find("signature guarantee is required"))                                          # reviewer highlight
p.insert_link({"kind": fitz.LINK_URI, "from": find("Account Application"), "uri": "https://example.com/account-application"})
a = p.add_text_annot(fitz.Point(560, 110), "Confirm this list with the business owner."); a.set_info(title="Reviewer"); a.update()
p.add_freetext_annot(fitz.Rect(400, 560, 570, 600), "Test comment: check the tax-waiver wording.", fontsize=9, fill_color=(1, 1, .8)).update()
p.add_stamp_annot(fitz.Rect(420, 620, 570, 670), stamp=0).update()
p.add_ink_annot([[(80, 700), (120, 690), (160, 705), (200, 692)]]).update()
d.save(os.path.join(here, "annotations.pdf"), garbage=3, deflate=True)

# --- barcodes.pdf
pdfmetrics.registerFont(TTFont("LibreBarcode39", os.path.join(src, "LibreBarcode39-Regular.ttf")))
W, H = letter; c = canvas.Canvas(os.path.join(here, "barcodes.pdf"), pagesize=letter)
c.setFont("Helvetica-Bold", 14); c.drawString(72, H - 72, "Barcode test page")
c.setFont("Helvetica", 10)
c.drawString(72, H - 110, "A. Code 39 drawn as vector rectangles:")
code39.Standard39("TEST1234", barHeight=36, barWidth=1.0, humanReadable=False, checksum=0).drawOn(c, 72, H - 160)
c.drawString(72, H - 200, "B. QR code drawn as vector squares:")
q = qr.QrCodeWidget("https://example.com/test"); b = q.getBounds(); s = 100
dr = Drawing(s, s, transform=[s / (b[2] - b[0]), 0, 0, s / (b[3] - b[1]), 0, 0]); dr.add(q); renderPDF.draw(dr, c, 72, H - 320)
c.drawString(72, H - 360, "C. Code 39 drawn as text in a barcode font:")
c.setFont("LibreBarcode39", 36); c.drawString(72, H - 410, "*TEST1234*")
c.setFont("Helvetica", 10); c.drawString(72, H - 450, "D. Decorative stripes (not a barcode):")
for i in range(12): c.rect(72 + i * 12, H - 490, 6, 30, stroke=0, fill=1)
c.save()
print("fixtures written to", here)
