import re
import os
from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORM_RECOGNIZER_KEY")

if not endpoint or not key:
    raise ValueError("Please set AZURE_FORM_RECOGNIZER_ENDPOINT and AZURE_FORM_RECOGNIZER_KEY environment variables.")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def parse_item_line(line):
    original_line = re.sub(r'\s+', ' ', line).strip()

    # Match weight anywhere in the line
    weight_pattern = re.compile(
        r'(\d+\.?\d*)\s*(kg|kilogram|kilograms|g|gram|grams|ml|millilitre|millilitres|l|litre|litres|liter|liters|pack|packs)',
        re.IGNORECASE
    )
    weight_match = weight_pattern.search(original_line)
    weight = weight_match.group(1) + weight_match.group(2) if weight_match else "N/A"

    # Extract price at end
    price_match = re.search(r'(\d+\.\d{2})\s*$', original_line)
    price = price_match.group(1) if price_match else "N/A"

    # Remove price from name
    name_part = original_line
    if price_match:
        name_part = name_part[:price_match.start()].strip()

    # Extract quantity if present
    qty = 1
    qty_match = re.search(r'(qty|quantity|x)\s?(\d+)', name_part, re.IGNORECASE)
    if qty_match:
        qty = int(qty_match.group(2))
        name_part = re.sub(r'(qty|quantity|x)\s?\d+', '', name_part, flags=re.IGNORECASE).strip()

    # Strip leading/trailing non-alphanumeric characters (keep letters, digits, spaces inside)
    clean_name = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', name_part)

    return {"name": clean_name, "qty": qty, "weight": weight.upper(), "price": price}


def extract_store_name(all_lines):
    for line in all_lines:
        if re.search(r'(coles)', line, re.IGNORECASE):
            return line.strip()
    return "Unknown"


def extract_total_amount(all_lines):
    for line in all_lines:
        match = re.search(r'Total\s+for\s+\d+\s+items:\s*\$?(\d+\.\d{2})', line, re.IGNORECASE)
        if match:
            return match.group(1)
    for i, line in enumerate(all_lines):
        if "TOTAL" in line.upper() and i + 1 < len(all_lines):
            next_line = all_lines[i + 1].replace("$", "").strip()
            if re.match(r'^\d+\.\d{2}$', next_line):
                return next_line
    return None


def print_receipt_items(path):
    with open(path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-receipt", document=f)
    result = poller.result()

    all_lines = [line.content.strip() for page in result.pages for line in page.lines]

    store_name = extract_store_name(all_lines)

    date_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
    date = next((m.group(1) for l in all_lines if (m := date_pattern.search(l))), None)

    total = extract_total_amount(all_lines)

    print(f"\nStore: {store_name}")
    print(f"Receipt Date: {date if date else 'Not found'}")
    print(f"Total Amount: ${total if total else 'Not found'}\n")

    item_lines = []
    capture = False
    for line in all_lines:
        if not capture and "Description" in line:
            capture = True
            continue
        if capture:
            if (re.search(r'\bTOTAL\b', line, re.IGNORECASE) or
                re.search(r'Total\s+for\s+\d+\s+items', line, re.IGNORECASE) or
                "SUBTOTAL" in line.upper()):
                break
            if line.strip():
                item_lines.append(line)

    parsed_items = []
    current_item = ""
    for l in item_lines:
        # Detect quantity line pattern like "2 @ $15.00 EACH"
        if re.match(r'^\d+\s*@\s*\$\d+\.\d{2}\s*EACH$', l.strip(), re.IGNORECASE):
            qty_match = re.match(r'^(\d+)\s*@\s*\$\d+\.\d{2}\s*EACH$', l.strip(), re.IGNORECASE)
            if qty_match and parsed_items:
                parsed_items[-1]['qty'] = int(qty_match.group(1))  # update quantity of last item
        else:
            # Accumulate item line until price found at end
            if current_item:
                current_item += " " + l
            else:
                current_item = l
            if re.search(r'\d+\.\d{2}$', current_item):
                parsed_items.append(parse_item_line(current_item))
                current_item = ""

    print("--- Receipt Items ---\n")
    for item in parsed_items:
        print(item)


if __name__ == "__main__":
    print_receipt_items(
        "/Users/rohitvalanki/ReceiptProcessingService/test/test-receipts/coles/e-receipts/receipt2.pdf"
    )
