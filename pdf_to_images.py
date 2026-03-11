# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pymupdf",
# ]
# ///

import fitz
from pathlib import Path


def extract_images(pdf_path: Path) -> None:
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
    print(f"Extracted images from {pdf_path.name} -> {out_dir.name}/")


downloads = Path.home() / "Downloads"
pdf_files = list(downloads.glob("*.pdf"))

if not pdf_files:
    print("No PDFs found in Downloads.")
for pdf in pdf_files:
    try:
        extract_images(pdf)
    except Exception as e:
        print(f"Error processing {pdf.name}: {e}")