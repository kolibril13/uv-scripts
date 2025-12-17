# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pymupdf",
# ]
# ///

import fitz  # pip install pymupdf
from pathlib import Path

pdf_path = Path.home() / "Downloads" / "input.pdf"
out_dir = pdf_path.with_suffix("")
out_dir.mkdir(exist_ok=True)

doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    for j, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n > 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(out_dir / f"page{i+1}_img{j+1}.png")
        pix = None

doc.close()