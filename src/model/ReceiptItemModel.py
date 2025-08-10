from dataclasses import dataclass
from typing import Optional

from src.model.WeightModel import Weight


@dataclass
class ReceiptItem:
    name: str
    qty: int = 1
    weight: Optional[Weight] = None
    price: Optional[float] = None
