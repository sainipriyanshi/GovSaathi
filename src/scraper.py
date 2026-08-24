# src/scraper.py
import requests
from bs4 import BeautifulSoup
import os
import json

RAW_DATA_DIR = "data/raw"
os.makedirs(RAW_DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. Scrape Income Tax Portal FAQs & Guidance
def scrape_income_tax():
    print("Scraping Income Tax Portal...")
    url = "https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/general-questions-0"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract main text paragraphs and heading blocks
            content_blocks = [p.get_text(strip=True) for p in soup.find_all(['p', 'h3', 'li']) if len(p.get_text(strip=True)) > 25]
            
            output_path = os.path.join(RAW_DATA_DIR, "incometax_portal_data.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(content_blocks))
            print(f"✅ Saved Income Tax data to {output_path}")
        else:
            print(f"❌ Income Tax scrape failed with status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Income Tax scrape error: {e}")


# 2. Scrape myScheme Portal FAQs & Public Scheme Details
def scrape_myscheme():
    print("Scraping myScheme Portal FAQs...")
    url = "https://www.myscheme.gov.in/faqs"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract FAQ sections
            faqs = []
            for q_elem in soup.find_all(['h3', 'div'], class_=lambda c: c and 'faq' in c.lower()):
                text = q_elem.get_text(strip=True)
                if text:
                    faqs.append(text)
            
            # Fallback text extract if class names are dynamic
            if not faqs:
                faqs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]

            output_path = os.path.join(RAW_DATA_DIR, "myscheme_portal_data.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(faqs))
            print(f"✅ Saved myScheme data to {output_path}")
        else:
            print(f"❌ myScheme scrape failed with status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ myScheme scrape error: {e}")

if __name__ == "__main__":
    scrape_income_tax()
    scrape_myscheme()