from dataclasses import dataclass
from typing import Optional

@dataclass
class ReceiptItem:
    name: str
    qty: int = 1
    weight: Optional[float] = None
    price: Optional[float] = None
