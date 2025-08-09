from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image
import pytesseract

def preprocess_image_cv(image):
    # Convert PIL image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def ocr_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    text = ""
    for page in pages:
        processed_img = preprocess_image_cv(page)
        pil_img = Image.fromarray(processed_img)
        text += pytesseract.image_to_string(pil_img) + "\n"
    return text

def ocr_receipt(path):
    if path.lower().endswith('.pdf'):
        return ocr_from_pdf(path)
    else:
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"File not found or not an image: {path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)
        return pytesseract.image_to_string(pil_img)

if __name__ == "__main__":
    receipt_path = "/Users/rohitvalanki/ReceiptProcessingService/src/tesseract/test-receipts/eReceipt_2596_Macarthur Chambers_02Aug2025__qwmfd.pdf"
    print(ocr_receipt(receipt_path))
