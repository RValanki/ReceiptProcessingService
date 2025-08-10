from dataclasses import dataclass

@dataclass
class ReceiptItem:
    name: str
    qty: int = 1
    weight: str = "N/A"
    price: str = "N/A"

