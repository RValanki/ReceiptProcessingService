from dataclasses import dataclass
from typing import List, Optional
from src.model import ReceiptItemModel

@dataclass
class Receipt:
    store_name: str
    date: Optional[str]
    total_amount: Optional[float]
    items: List[ReceiptItemModel]
