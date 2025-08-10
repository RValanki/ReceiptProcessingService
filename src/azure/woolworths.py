import re
import os
import dataclasses
import json
import sys

from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ClientAuthenticationError

from src.model.ReceiptModel import Receipt
from src.model.ReceiptItemModel import ReceiptItem

load_dotenv()

endpoint = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORM_RECOGNIZER_KEY")

if not endpoint or not key:
    raise ValueError("Please set AZURE_FORM_RECOGNIZER_ENDPOINT and AZURE_FORM_RECOGNIZER_KEY environment variables.")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def parse_item_line(line) -> ReceiptItem:
    # Extract weight as grams (float)
    weight = None
    weight_match = re.search(r'(\d+\.?\d*)\s?(kg|g|ml|l)', line, re.IGNORECASE)
    if weight_match:
        num = float(weight_match.group(1))
        unit = weight_match.group(2).lower()
        if unit.startswith('kg'):
            weight = num * 1000
        elif unit.startswith('g'):
            weight = num
        elif unit.startswith('l'):
            weight = num * 1000
        elif unit.startswith('ml'):
            weight = num

    # Extract price as float
    price = None
    price_match = re.search(r'(\d+\.\d{2})\s*$', line)
    if price_match:
        price = float(price_match.group(1))

    # Remove price and weight from the name
    name_part = line
    if price_match:
        name_part = name_part[:price_match.start()].strip()
    if weight_match:
        name_part = name_part.replace(weight_match.group(0), '').strip()

    # Extract quantity
    qty = 1
    qty_match = re.search(r'(qty|quantity|x)\s?(\d+)', name_part, re.IGNORECASE)
    if qty_match:
        qty = int(qty_match.group(2))
        name_part = re.sub(r'(qty|quantity|x)\s?\d+', '', name_part, flags=re.IGNORECASE).strip()

    # Clean name
    clean_name = re.sub(r'[^A-Za-z0-9 ]+', '', name_part)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()

    return ReceiptItem(
        name=clean_name,
        qty=qty,
        weight=weight,
        price=price
    )



def parse_receipt_items(path) -> Receipt:
    try:
        with open(path, "rb") as f:
            poller = client.begin_analyze_document("prebuilt-receipt", document=f)
        result = poller.result()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found - {path}")
    except ClientAuthenticationError:
        raise RuntimeError("Authentication failed: Check your Azure Form Recognizer key and endpoint.")
    except ServiceRequestError as e:
        raise RuntimeError(f"Network error: {e}. Please check your internet connection.")
    except HttpResponseError as e:
        raise RuntimeError(f"Service returned an error: {e.message}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

    all_lines = []
    for page in result.pages:
        for line in page.lines:
            all_lines.append(line.content.strip())

    # Store name is the very last line of the receipt
    store_name = all_lines[-1] if all_lines else "Unknown"

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
                total = float(next_line)
                break

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

    # Parse items into models
    parsed_items = [parse_item_line(item_line) for item_line in combined_items]

    return Receipt(
        store_name=store_name,
        date=date,
        total_amount=total,
        items=parsed_items
    )


import sys

if __name__ == "__main__":
    default_path = "/Users/rohitvalanki/ReceiptProcessingService/test/test-receipts/woolworths/e-receipts/eReceipt_3168_Endeavour%20Hills_03Feb2025__xjifb.pdf"
    receipt_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    receipt = parse_receipt_items(receipt_path)
    receipt_dict = dataclasses.asdict(receipt)
    print(json.dumps(receipt_dict, indent=4))

