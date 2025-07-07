from enum import Enum

class AttributeType(Enum):
    BENEFICIAL = 1
    HARMFUL = 2
    RATIO = 3

class NOVACategory(Enum):
    MINIMALLY_PROCESSED = 1
    PROCESSED_CULINARY_INGREDIENTS = 2
    PROCESSED_FOODS = 3
    ULTRA_PROCESSED_FOODS = 4