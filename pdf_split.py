# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pypdf",
# ]
# ///

from pathlib import Path
from pypdf import PdfReader, PdfWriter

def split_pdf(pdf_path: Path, split_after_page: int = 3) -> None:
    """
    Split pdf_path into two files:
      - part 1: pages 1 .. split_after_page
      - part 2: pages (split_after_page + 1) .. end

    split_after_page is 1-based.
    """
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)

    if total <= split_after_page:
        print(f"Skipping {pdf_path.name}: only {total} pages (need > {split_after_page}).")
        return

    # Part 1: pages 0 .. split_after_page-1 (zero-based in pypdf)
    part1 = PdfWriter()
    for i in range(0, split_after_page):
        part1.add_page(reader.pages[i])

    # Part 2: pages split_after_page .. total-1
    part2 = PdfWriter()
    for i in range(split_after_page, total):
        part2.add_page(reader.pages[i])

    # Output files
    p1_out = pdf_path.with_stem(f"{pdf_path.stem}_part1_1-{split_after_page}")
    p2_out = pdf_path.with_stem(f"{pdf_path.stem}_part2_{split_after_page+1}-{total}")

    with p1_out.open("wb") as f:
        part1.write(f)
    with p2_out.open("wb") as f:
        part2.write(f)

    print(f"Split {pdf_path.name} -> {p1_out.name}, {p2_out.name} (total {total} pages)")

if __name__ == "__main__":
    downloads = Path.home() / "Downloads"
    pdf_files = list(downloads.glob("*.pdf"))

    if not pdf_files:
        print("No PDFs found in Downloads.")
    for pdf in pdf_files:
        try:
            split_pdf(pdf, split_after_page=3)
        except Exception as e:
            print(f"Error processing {pdf.name}: {e}")
