# src/scraper.py
import json
import os
import re

import requests
from bs4 import BeautifulSoup

RAW_DATA_DIR = "data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

# Pages that are real, static, and about actual tax rules (not e-Pay/challan UI).
# Add more from this same domain as you find them.
INCOME_TAX_URLS = [
    "https://www.incometax.gov.in/iec/foportal/help/new-tax-vs-old-tax-regime-faqs",
    "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1",
    "https://www.incometax.gov.in/iec/foportal/help/e-filing-itr2-form-faq",
    "https://www.incometaxindia.gov.in/w/deductions",
    "https://www.incometaxindia.gov.in/w/deductions-allowable-to-tax-payer",
    # PDF, not HTML — needs a separate extraction path, see scrape_pdf_faq() below
    "https://www.incometax.gov.in/iec/foportal/sites/default/files/2024-06/Common%20ITR%20Filing%20FAQs%20AY%202024-25.pdf",
]


def scrape_income_tax_page(url: str) -> list[dict]:
    """
    Scrapes ONE incometax.gov.in page and returns a list of {question, answer,
    source_url} records.

    These pages are inconsistent: some use <h3>/<h4> for questions, others
    (like new-tax-vs-old-tax-regime-faqs) use plain numbered bold paragraphs
    ("1. Question text" inside <p><strong>). Rather than depend on a specific
    tag, extract all visible text and split on the numbered-question pattern
    directly, then filter out short nav/breadcrumb noise by length.
    """
    print(f"Scraping: {url}")
    records = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  Failed with status {response.status_code}")
            return records

        soup = BeautifulSoup(response.text, "html.parser")

        # Drop nav/header/footer tags outright — cuts most boilerplate before
        # we even get to text extraction.
        for tag in soup(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        full_text = soup.get_text("\n", strip=True)

        # Trim trailing footer content that isn't wrapped in a <footer> tag
        for marker in ["Follow us on", "Last reviewed and updated on"]:
            if marker in full_text:
                full_text = full_text.split(marker)[0]

        # Strategy 1: "Ans:" marker anchoring — most reliable when present
        records = _extract_ans_marked_qa(full_text, url)

        # Strategy 2: numbered question markers ("1. ", "12. ")
        if len(records) < 3:
            pattern = re.compile(r"\n\s*(\d{1,2})\.\s+", re.MULTILINE)
            matches = list(pattern.finditer(full_text))
            numbered_records = _extract_blocks(full_text, matches, url)
            if len(numbered_records) > len(records):
                records = numbered_records

        # Strategy 3: fallback — split on "?" line endings
        if len(records) < 3:
            print(f"  Trying fallback split")
            qmark_pattern = re.compile(r"(?<=\?)\s*\n+")
            fragments = qmark_pattern.split(full_text)
            fallback_records = []
            for frag in fragments:
                frag = frag.strip()
                if len(frag) < 60 or "?" not in frag:
                    continue
                q_match = re.match(r"^(.*?\?)\s*(.*)$", frag, re.S)
                if q_match and len(q_match.group(2).strip()) > 15:
                    fallback_records.append({
                        "question": q_match.group(1).strip(),
                        "answer": q_match.group(2).strip(),
                        "source_url": url,
                        "assessment_year": None,
                        "tax_year": None,
                    })
            if len(fallback_records) > len(records):
                records = fallback_records

        print(f"  Extracted {len(records)} Q&A pairs")
    except Exception as e:
        print(f"  Error: {e}")

    return records


def _split_trailing_question(text: str):
    """Returns (body, trailing_question). trailing_question is the last
    '...?' sentence near the END of text (within ~50 chars of the end);
    otherwise assumes no clean trailing question is present."""
    matches = list(re.finditer(r"[^?]*\?", text, re.S))
    if not matches:
        return text.strip(), ""
    last = matches[-1]
    remainder_after = text[last.end():]
    if len(remainder_after.strip()) > 50:
        return text.strip(), ""  # "?" wasn't near the end — not a clean trailing question
    return text[:last.start()].strip(), text[last.start():last.end()].strip()


def _extract_ans_marked_qa(full_text: str, url: str) -> list[dict]:
    """
    These government pages consistently prefix every answer with a literal
    'Ans:' marker. That's a far more reliable anchor than numbered markers
    or bare question-marks (which misfire when a page has no numbering, or
    when answer text itself contains '?').
    """
    ans_markers = list(re.finditer(r"\bans\.?\s*:\s*", full_text, re.IGNORECASE))
    if len(ans_markers) < 3:
        return []  # not enough markers to trust this strategy for this page

    starts = [0] + [m.end() for m in ans_markers]
    ends = [m.start() for m in ans_markers] + [len(full_text)]
    segments = [full_text[s:e] for s, e in zip(starts, ends)]

    records = []
    _, pending_question = _split_trailing_question(segments[0])

    for i in range(1, len(segments)):
        is_last = (i == len(segments) - 1)
        if is_last:
            answer_body, next_question = segments[i].strip(), ""
        else:
            answer_body, next_question = _split_trailing_question(segments[i])

        if pending_question and answer_body and len(answer_body) > 15:
            records.append({
                "question": pending_question,
                "answer": answer_body,
                "source_url": url,
                "assessment_year": None,
                "tax_year": None,
            })
        pending_question = next_question

    return records


def _extract_blocks(full_text: str, matches: list, url: str) -> list[dict]:
    records = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        block = full_text[start:end].strip()

        if len(block) < 60:
            continue

        q_match = re.match(r"^(.*?\?)\s*(.*)$", block, re.S)
        if q_match:
            question, answer = q_match.group(1).strip(), q_match.group(2).strip()
        else:
            words = block.split()
            question = " ".join(words[:15])
            answer = block

        if answer:
            records.append({
                "question": question,
                "answer": answer,
                "source_url": url,
                "assessment_year": None,
                "tax_year": None,
            })
    return records


def scrape_pdf_faq(url: str) -> list[dict]:
    """
    For .pdf URLs — BeautifulSoup can't parse PDF bytes, so download and
    extract text with pypdf instead. Falls back to one big chunk per PDF
    since numbered-question structure varies more in PDFs than HTML pages.
    """
    import io
    from pypdf import PdfReader

    print(f"Scraping PDF: {url}")
    records = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"  Failed with status {response.status_code}")
            return records

        reader = PdfReader(io.BytesIO(response.content))
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # Strategy 1: "Ans:" marker anchoring — this PDF uses it consistently
        records = _extract_ans_marked_qa(full_text, url)
        for r in records:
            r["assessment_year"] = "AY 2024-25"

        # Strategy 2: numbered questions ("1.", "1)", "Q1.") if Ans: didn't work
        if len(records) < 3:
            question_pattern = re.compile(r"\n\s*(?:Q\.?\s*)?\d{1,3}[\.\)]\s+")
            parts = question_pattern.split(full_text)
            if len(parts) > 1:
                records = []
                for part in parts[1:]:
                    part = part.strip()
                    if len(part) > 20:
                        records.append({
                            "question": None,
                            "answer": part,
                            "source_url": url,
                            "assessment_year": "AY 2024-25",
                            "tax_year": None,
                        })

        if not records:
            # Couldn't detect Q&A structure — store as one block, still citable
            records.append({
                "question": None,
                "answer": full_text.strip(),
                "source_url": url,
                "assessment_year": "AY 2024-25",
                "tax_year": None,
            })

        print(f"  Extracted {len(records)} block(s)")
    except Exception as e:
        print(f"  Error: {e}")

    return records


def scrape_income_tax():
    all_records = []
    for url in INCOME_TAX_URLS:
        if url.lower().endswith(".pdf"):
            all_records.extend(scrape_pdf_faq(url))
        else:
            all_records.extend(scrape_income_tax_page(url))

    output_path = os.path.join(RAW_DATA_DIR, "incometax_faqs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_records)} total Q&A records to {output_path}")


# myScheme.gov.in is a Next.js SPA: FAQ answers only render client-side via JS,
# and requests/BeautifulSoup only see the collapsed question headings with no
# answers. Actual scheme data (eligibility/benefits/documents) also isn't on
# static HTML here. Use the pre-scraped `shrijayan/gov_myscheme` HuggingFace
# dataset instead — see download instructions from earlier in this project.
def scrape_myscheme():
    print(
        "Skipping live myScheme scrape: myscheme.gov.in is a JS-rendered SPA "
        "and plain requests/BeautifulSoup cannot retrieve FAQ answers or scheme "
        "details from it. Use the 'shrijayan/gov_myscheme' HuggingFace dataset "
        "instead (see load_dataset() instructions) and place the exported JSON "
        "directly into data/raw/."
    )


if __name__ == "__main__":
    scrape_income_tax()
    scrape_myscheme()