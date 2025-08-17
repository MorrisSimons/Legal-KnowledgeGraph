import requests
import json
import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import math

API_URL = "https://rattspraxis.etjanst.domstol.se/api/v1/sok"


HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Number of pages to scrape
CASES_PER_PAGE = 50
NUM_PAGES = 3

all_cases = []

os.makedirs('cases', exist_ok=True)

def download_pdf_bilagor(fillagringId, dest_path):
    url_encoded_id = urllib.parse.quote(fillagringId, safe='')
    pdf_url = f"https://rattspraxis.etjanst.domstol.se/api/v1/bilagor/{url_encoded_id}"
    try:
        r = requests.get(pdf_url, stream=True)
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded PDF: {dest_path}")
        return True
    except Exception as e:
        print(f"Failed to download {pdf_url}: {e}")
        return False

def get_case_full_text_selenium(case_url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(case_url)
        time.sleep(3)
        # Try to click the "Visa mer innehåll" button if it exists
        button_clicked = False
        try:
            show_more = driver.find_element(By.XPATH, "//button[contains(text(), 'Visa mer innehåll')]")
            show_more.click()
            button_clicked = True
        except Exception:
            try:
                show_more = driver.find_element(By.XPATH, "//*[contains(text(), 'Visa mer innehåll')]")
                show_more.click()
                button_clicked = True
            except Exception:
                print("No 'Visa mer innehåll' button found.")
        if button_clicked:
            print("'Visa mer innehåll' button clicked, waiting for content to expand...")
            time.sleep(4)
        # Print all divs' text lengths for debug
        divs = driver.find_elements(By.TAG_NAME, 'div')
        for i, div in enumerate(divs):
            text = div.text.strip()
            print(f"DEBUG: div[{i}] text length: {len(text)}")
        # Now extract the largest div's text as before
        main_text = ''
        max_len = 0
        for div in divs:
            text = div.text.strip()
            if len(text) > max_len:
                main_text = text
                max_len = len(text)
        if "Laserpekaren" in main_text:
            print("DEBUG: Extracted text for Laserpekaren IV:")
            print(main_text)
        return main_text
    except Exception as e:
        print(f"Failed to get full text from {case_url}: {e}")
        return ""
    finally:
        driver.quit()

def process_case(case, case_dir, pdf_dir):
    # Get full text from public page
    if case['case_url']:
        case['full_text'] = get_case_full_text_selenium(case['case_url'])
    else:
        case['full_text'] = ""
    # Save individual case JSON
    with open(os.path.join(case_dir, f"{case['case_number']}.json"), 'w', encoding='utf-8') as f:
        json.dump(case, f, ensure_ascii=False, indent=2)
    print(f"Saving case {case['case_number']} with full_text length: {len(case['full_text'])}")
    # Download PDFs
    for pdf in case['pdf_documents']:
        fillagringId = pdf['file_id']
        filename = pdf['filename'] or fillagringId.replace('/', '_')
        dest_path = os.path.join(pdf_dir, filename)
        download_pdf_bilagor(fillagringId, dest_path)


for page in range(NUM_PAGES):
    payload = {
        "antalPerSida": CASES_PER_PAGE,
        "asc": False,
        "filter": {
            "domstolKodLista": ["HDO"],
            
        },
        "sidIndex": page,
        "sokfras": {"andLista": [], "notLista": [], "orLista": []},
        "sortorder": "avgorandedatum"
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    data = response.json()
    if page == 0:
        print("First page API response (truncated):", json.dumps(data, ensure_ascii=False)[:1000])
    for item in data.get("publiceringLista", []):
        case_id = item.get("id", "")
        case_number = item.get("malNummerLista", [""])[0] if item.get("malNummerLista") else ""
        if not case_number:
            continue
        nickname = item.get("benamning", "")
        summary = item.get("sammanfattning", "") or item.get("rubrik", "") or ""
        decision_date = item.get("avgorandedatum", "")
        publication_time = item.get("publiceringstid", "")
        case_type = item.get("typ", "")
        is_precedent = item.get("arVagledande", False)
        court = item.get("domstol", {}).get("domstolNamn", "")
        court_code = item.get("domstol", {}).get("domstolKod", "")
        keywords = item.get("nyckelordLista", [])
        legal_areas = item.get("rattsomradeLista", [])
        legal_references = [
            {
                "reference": ref.get("referens", ""),
                "sfs_number": ref.get("sfsNummer", "")
            } for ref in item.get("lagrumLista", [])
        ]
        referenced_publications = [pub.get("fritext", "") for pub in item.get("hanvisadePubliceringarLista", [])]
        pdf_documents = [
            {
                "filename": pdf.get("filnamn", ""),
                "file_id": pdf.get("fillagringId", ""),
            } for pdf in item.get("bilagaLista", [])
        ]
        correlation_number = item.get("gruppKorrelationsnummer", "")
        case_url = f"https://rattspraxis.etjanst.domstol.se/sok/publicering/{correlation_number}" if correlation_number else ""
        case = {
            "case_number": case_number,
            "nickname": nickname,
            "summary": summary,
            "decision_date": decision_date,
            "publication_time": publication_time,
            "case_id": case_id,
            "type": case_type,
            "is_precedent": is_precedent,
            "court": court,
            "court_code": court_code,
            "keywords": keywords,
            "legal_areas": legal_areas,
            "legal_references": legal_references,
            "referenced_publications": referenced_publications,
            "pdf_documents": pdf_documents,
            "case_url": case_url,
            "correlation_number": correlation_number
        }
        all_cases.append(case)
        # Save and download per case
        case_dir = os.path.join('cases', case_number)
        os.makedirs(case_dir, exist_ok=True)
        pdf_dir = os.path.join(case_dir, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        process_case(case, case_dir, pdf_dir)
    time.sleep(15)

