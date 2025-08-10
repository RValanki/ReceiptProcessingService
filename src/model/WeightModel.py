from dataclasses import dataclass
from enum import Enum

class WeightUnit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITRE = "ml"
    LITRE = "l"
    PACK = "pack"
    PACKS = "packs"

@dataclass
class Weight:
    value: float
    unit: WeightUnit