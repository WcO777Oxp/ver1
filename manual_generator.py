import os
import re
import numpy as np
import cv2
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image, ImageOps
import pytesseract

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
POPPLER_PATH = os.path.join(BASE_DIR, "res", "poppler", "Library", "bin")
TESSERACT_PATH = os.path.join(BASE_DIR, "res", "Tesseract-OCR")

PDF_RES = os.path.join(BASE_DIR, "res")
OUTPUT_DIR = os.path.join(PDF_RES, "images")
TOC_SCAN_PAGES = 8

def clean_filename(name):
    name = re.sub(r"[^\w\s-]", "", name).strip().lower().replace(" ", "_")
    name = re.sub(r"_+", "_", name)
    return name

def crop_image(pil_img):
    return pil_img  # Cropping disabled for now

def extract_titles_from_toc(text_lines):
    titles = []
    for line in text_lines:
        line = line.strip()
        match = re.match(r"^(.*?)\s*\.{3,}\s*(\d{1,3})$", line)
        if not match:
            match = re.match(r"^(.*?)\s{2,}(\d{1,3})$", line)
        if match:
            title = match.group(1).strip()
            page = int(match.group(2).strip())
            titles.append((title, page))
    return titles

def extract_toc_from_pdf(pdf_path):
    toc_lines = []
    try:
        reader = PdfReader(pdf_path)
        for i in range(min(TOC_SCAN_PAGES, len(reader.pages))):
            text = reader.pages[i].extract_text()
            if text:
                toc_lines.extend(text.splitlines())
    except:
        pass

    if not toc_lines:
        print("❗ TOC text extraction failed. Trying OCR fallback...")
        try:
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=TOC_SCAN_PAGES, poppler_path=POPPLER_PATH)
            for img in images:
                img = ImageOps.grayscale(img)
                img = ImageOps.autocontrast(img)
                text = pytesseract.image_to_string(img)
                toc_lines.extend(text.splitlines())
        except Exception as e:
            print(f"OCR TOC extraction failed: {e}")

    return extract_titles_from_toc(toc_lines)

def save_guidelines_per_manual(titles_by_pdf):
    for pdf_name, titles in titles_by_pdf.items():
        if "RETAIL" in pdf_name.upper():
            file_name = "retail_guideline.txt"
        elif "POSWEB" in pdf_name.upper():
            file_name = "posweb_guideline.txt"
        else:
            continue  # Skip unknown manual types

        output_path = os.path.join("res", file_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        titles = list(dict.fromkeys(titles))  # Deduplicate
        with open(output_path, "w", encoding="utf-8") as f:
            for title in titles:
                f.write(f"• {title.strip()}\n")
        print(f" Saved guideline: {output_path}")

def extract_helpful_summary(text):
    if not text:
        return "This page contains general POS instructions."
    for line in text.strip().splitlines():
        line = line.strip()
        if len(line.split()) > 3 and not line.isupper():
            return f"This section explains: {line}"
    return "This section contains important POS instructions."

def generate_images_from_toc(pdf_path, output_dir, collected_titles):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n Rendering from TOC: {pdf_path}")

    toc = extract_toc_from_pdf(pdf_path)
    if not toc:
        print(" No TOC entries found.")
        return

    try:
        pages = convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)
        reader = PdfReader(pdf_path)
    except Exception as e:
        print(f" Failed to read PDF: {e}")
        return

    used_filenames = set()

    for i in range(len(toc)):
        title, start_page = toc[i]
        end_page = toc[i + 1][1] - 1 if i + 1 < len(toc) else len(pages)
        base_filename = clean_filename(title)

        collected_titles.append(title)

        for j, page_num in enumerate(range(start_page, end_page + 1)):
            index = page_num - 1
            if index < 0 or index >= len(pages):
                continue

            image = crop_image(pages[index])
            filename = f"{base_filename}({j + 1})"
            while filename in used_filenames:
                filename += "_alt"
            used_filenames.add(filename)

            image_path = os.path.join(output_dir, f"{filename}.png")
            text_path = os.path.join(output_dir, f"{filename}.txt")

            try:
                image.save(image_path)
                print(f" Saved image: {image_path}")
            except Exception as e:
                print(f"❌ Failed to save image {image_path}: {e}")

            try:
                text = reader.pages[index].extract_text()
                if not text:
                    text = pytesseract.image_to_string(ImageOps.autocontrast(ImageOps.grayscale(pages[index])))

                summary = extract_helpful_summary(text)
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(f"[GUIDELINE] {summary}\n\n{title}\n\n{text.strip()}" if text else f"[GUIDELINE] {summary}\n\n{title}")
                print(f" Saved text: {text_path}")
            except Exception as e:
                print(f" Failed to extract/save text for page {page_num}: {e}")

def run_manual_import():
    pdfs = sorted(f for f in os.listdir(PDF_RES) if f.lower().endswith(".pdf"))
    if not pdfs:
        print(" No PDF files found.")
        return

    processed = []
    skipped = []
    all_titles_by_pdf = {}

    for pdf in pdfs:
        pdf_path = os.path.join(PDF_RES, pdf)
        pdf_name = os.path.splitext(pdf)[0]
        output_dir = os.path.join(OUTPUT_DIR, pdf_name)

        if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
            print(f" Skipping already processed: {pdf}")
            skipped.append(pdf)
            continue

        print(f" Processing PDF: {pdf}")
        all_titles_by_pdf[pdf_name] = []
        generate_images_from_toc(pdf_path, output_dir, all_titles_by_pdf[pdf_name])
        processed.append(pdf)

    if all_titles_by_pdf:
        save_guidelines_per_manual(all_titles_by_pdf)

    print("\n Finished processing.")
    if processed:
        print(" Processed:")
        for p in processed:
            print(f"  • {p}")
    if skipped:
        print("\n Skipped:")
        for s in skipped:
            print(f"  • {s}")
