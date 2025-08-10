import re
import os
import dataclasses
import json
import sys
from typing import Optional

from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ClientAuthenticationError

from src.model.ReceiptModel import Receipt
from src.model.ReceiptItemModel import ReceiptItem
from src.model.WeightModel import Weight, WeightUnit  # Import your Weight classes

load_dotenv()

endpoint = os.environ.get("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORM_RECOGNIZER_KEY")

if not endpoint or not key:
    raise ValueError("Please set AZURE_FORM_RECOGNIZER_ENDPOINT and AZURE_FORM_RECOGNIZER_KEY environment variables.")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def parse_weight(weight_match) -> Optional[Weight]:
    if not weight_match:
        return None
    num = float(weight_match.group(1))
    unit_str = weight_match.group(2).lower()

    if unit_str.startswith("kg"):
        unit = WeightUnit.KILOGRAM
    elif unit_str.startswith("g"):
        unit = WeightUnit.GRAM
    elif unit_str.startswith("ml"):
        unit = WeightUnit.MILLILITRE
    elif unit_str.startswith("l"):
        unit = WeightUnit.LITRE
    elif unit_str.startswith("pack"):
        unit = WeightUnit.PACKS if unit_str.endswith("s") else WeightUnit.PACK
    else:
        unit = None

    if unit is None:
        return None

    return Weight(value=num, unit=unit)


def parse_item_line(line) -> ReceiptItem:
    original_line = re.sub(r'\s+', ' ', line).strip()

    weight_pattern = re.compile(
        r'(\d+\.?\d*)\s*(kg|kilogram|kilograms|g|gram|grams|ml|millilitre|millilitres|l|litre|litres|liter|liters|pack|packs)',
        re.IGNORECASE
    )
    weight_match = weight_pattern.search(original_line)
    weight = parse_weight(weight_match)

    price_match = re.search(r'(\d+\.\d{2})\s*$', original_line)
    price = float(price_match.group(1)) if price_match else None

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

    # Clean name (remove leading/trailing non-alphanum)
    clean_name = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', name_part)

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

    all_lines = [line.content.strip() for page in result.pages for line in page.lines]

    # Store name usually last line
    store_name = all_lines[-1] if all_lines else "Unknown"

    # Extract date (DD/MM/YYYY)
    date_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
    date = next((m.group(1) for l in all_lines if (m := date_pattern.search(l))), None)

    # Extract total amount by looking for "TOTAL" line followed by numeric line
    total = None
    for i, line in enumerate(all_lines):
        if line.upper() == "TOTAL" and i + 1 < len(all_lines):
            next_line = all_lines[i + 1].replace("$", "").strip()
            if re.match(r'^\d+\.\d{2}$', next_line):
                total = float(next_line)
                break

    # Parse items between "Description" and "Promotional Price" or "SUBTOTAL"
    item_lines = []
    capture = False
    for line in all_lines:
        if not capture and "Description" in line:
            capture = True
            continue
        if capture:
            if "Promotional Price" in line or "SUBTOTAL" in line:
                break
            if line.strip():
                item_lines.append(line)

    # Combine lines until price found at end for each item
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

    parsed_items = [parse_item_line(item_line) for item_line in combined_items]

    return Receipt(
        store_name=store_name,
        date=date,
        total_amount=total,
        items=parsed_items
    )


if __name__ == "__main__":
    default_path = "/Users/rohitvalanki/ReceiptProcessingService/test/test-receipts/woolworths/e-receipts/eReceipt_3168_Endeavour%20Hills_03Feb2025__xjifb.pdf"
    receipt_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    receipt = parse_receipt_items(receipt_path)
    receipt_dict = dataclasses.asdict(receipt)
    print(json.dumps(receipt_dict, indent=4))
