import re
import os
from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

# Read key and endpoint from environment variables
endpoint = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORM_RECOGNIZER_KEY")

if not endpoint or not key:
    raise ValueError("Please set AZURE_FORM_RECOGNIZER_ENDPOINT and AZURE_FORM_RECOGNIZER_KEY environment variables.")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def parse_item_line(line):
    weight_match = re.search(r'(\d+\.?\d*\s?(kg|g|ml|l))', line, re.IGNORECASE)
    weight = weight_match.group(1) if weight_match else "N/A"

    price_match = re.search(r'(\d+\.\d{2})\s*$', line)
    price = price_match.group(1) if price_match else "N/A"

    # Remove price and weight from line to isolate name and qty
    name_part = line
    if price != "N/A":
        name_part = name_part[:price_match.start()].strip()
    if weight != "N/A":
        name_part = name_part.replace(weight, '').strip()

    qty = 1
    qty_match = re.search(r'(qty|quantity|x)\s?(\d+)', name_part, re.IGNORECASE)
    if qty_match:
        qty = qty_match.group(2)
        name_part = re.sub(r'(qty|quantity|x)\s?\d+', '', name_part, flags=re.IGNORECASE).strip()

    # Clean item name to only alphanumeric characters and spaces
    clean_name = re.sub(r'[^A-Za-z0-9 ]+', '', name_part)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()

    return {"name": clean_name, "qty": qty, "weight": weight, "price": price}

def print_receipt_items(path):
    with open(path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-receipt", document=f)
    result = poller.result()

    all_lines = []
    for page in result.pages:
        for line in page.lines:
            all_lines.append(line.content.strip())

    # Extract date (DD/MM/YYYY)
    date_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
    date = None
    for line in all_lines:
        match = date_pattern.search(line)
        if match:
            date = match.group(1)
            break

    # Extract total by finding "TOTAL" then reading next line if numeric amount
    total = None
    for i, line in enumerate(all_lines):
        if line.upper() == "TOTAL" and i + 1 < len(all_lines):
            next_line = all_lines[i + 1].replace("$", "").strip()
            if re.match(r'^\d+\.\d{2}$', next_line):
                total = next_line
                break

    print(f"\nReceipt Date: {date if date else 'Not found'}")
    print(f"Total Amount: ${total if total else 'Not found'}\n")

    # Parse items between Description and Promotional Price / SUBTOTAL
    start_parsing = False
    stop_parsing = False
    item_lines = []

    for line in all_lines:
        if not start_parsing and "Description" in line:
            start_parsing = True
            continue

        if start_parsing:
            if "Promotional Price" in line or "SUBTOTAL" in line:
                stop_parsing = True
                break
            if line == "":
                continue
            item_lines.append(line)

        if stop_parsing:
            break

    # Combine lines into full item lines (until price found at end)
    combined_items = []
    current_item = ""

    for l in item_lines:
        if current_item:
            current_item += " " + l
        else:
            current_item = l

        if re.search(r'\d+\.\d{2}$', current_item):
            combined_items.append(current_item.strip())
            current_item = ""

    if current_item:
        combined_items.append(current_item.strip())

    # Parse and print each item line
    print("--- Receipt Items ---\n")
    for item_line in combined_items:
        item = parse_item_line(item_line)
        print(item)

if __name__ == "__main__":
    print_receipt_items("/Users/rohitvalanki/ReceiptProcessingService/test/test-receipts/woolworths/e-receipts/eReceipt_3168_Endeavour%20Hills_03Feb2025__xjifb.pdf")
