import fitz  # PyMuPDF
import os
import json
import re
from collections import Counter

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def load_pdf(file_path):
    return fitz.open(file_path)

def extract_text_spans(doc):
    spans = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                line_spans = [span for span in line.get("spans", []) if span.get("text", "").strip()]
                if not line_spans:
                    continue
                line_text = " ".join(span["text"] for span in line_spans)
                max_size = max(span["size"] for span in line_spans)
                for span in line_spans:
                    text = span.get("text", "").strip()
                    spans.append({
                        "text": text,
                        "font_size": round(span["size"], 1),
                        "font": span["font"],
                        "bold": "Bold" in span["font"] or (span.get("flags", 0) & 2),
                        "page": page_num,
                        "line_text": line_text,
                        "line_size": round(max_size, 1)
                    })
    return spans

def get_font_level_mapping(spans):
    font_counter = Counter()
    for span in spans:
        font_counter[span["line_size"]] += 1

    sorted_fonts = sorted(font_counter.items(), key=lambda x: (-x[0], -x[1]))

    size_to_level = {}
    for i, (size, _) in enumerate(sorted_fonts):
        if i == 0:
            size_to_level[size] = "Title"
        elif i == 1:
            size_to_level[size] = "H1"
        elif i == 2:
            size_to_level[size] = "H2"
        elif i == 3:
            size_to_level[size] = "H3"
        elif i == 4:
            size_to_level[size] = "H4"
        else:
            size_to_level[size] = f"H{i}"

    return size_to_level

def is_valid_heading(text):
    text = text.strip()
    if not text or len(text) > 150:
        return False
    if text.replace(" ", "").isdigit():
        return False
    if re.fullmatch(r"[\-\u2013\u2014\s]*", text):
        return False
    return True

def assign_heading_levels(spans):
    size_to_level = get_font_level_mapping(spans)

    structured = {
        "title": "",
        "outline": []
    }

    seen_lines = set()
    title_lines = [s["line_text"] for s in spans if size_to_level.get(s["line_size"]) == "Title" and s["page"] == 0]
    structured["title"] = " ".join(sorted(set(title_lines), key=title_lines.index)).strip()

    for span in spans:
        text = span["line_text"].strip()
        level = size_to_level.get(span["line_size"])
        page = span["page"]

        if not is_valid_heading(text):
            continue

        if (text, page) in seen_lines:
            continue
        seen_lines.add((text, page))

        if level and level != "Title":
            structured["outline"].append({
                "level": level,
                "text": text,
                "page": page
            })

    return structured

def process_pdf_file(pdf_file):
    print(f"📄 Processing: {pdf_file}")
    pdf_path = os.path.join(INPUT_DIR, pdf_file)
    doc = load_pdf(pdf_path)
    spans = extract_text_spans(doc)
    result = assign_heading_levels(spans)

    output_filename = os.path.splitext(pdf_file)[0] + ".json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {output_filename}\n")

if __name__ == "__main__":
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".pdf"):
            process_pdf_file(file)
