from dataclasses import dataclass, field
from typing import Dict, Optional
from .category import Category

@dataclass
class Food:
    food_id: int
    food_name: str
    serving_size: float
    nutrients: Dict[str, float] = field(default_factory=dict)
    fvnl_percent: float = 0.0
    
    # Category assignment (can be auto-determined)
    category: Optional[Category] = None
    food_group_id: Optional[int] = None  # CNF food group ID for category determination
    
    # Category assignment metadata
    category_confidence: float = field(default=0.0, init=False)
    category_source: str = field(default="unknown", init=False)

    def __post_init__(self):
        """Auto-assign category if not provided and we have sufficient data"""
        if self.category is None and self.food_group_id is not None:
            self._assign_category()

    def _assign_category(self):
        """Assign HSR category based on food group and name"""
        try:
            from ..utils.food_group_mapper import FoodGroupMapper
            
            self.category = FoodGroupMapper.get_category(
                self.food_group_id, self.food_name
            )
            self.category_confidence = 0.9  # High confidence for automatic assignment
            self.category_source = "auto_assigned"
            
        except Exception as e:
            # Fallback to FOOD category if assignment fails
            self.category = Category.FOOD
            self.category_confidence = 0.3  # Low confidence for fallback
            self.category_source = f"fallback_due_to_error: {str(e)}"

    def assign_category_manually(self, category: Category, confidence: float = 1.0):
        """Manually assign category with confidence score"""
        self.category = category
        self.category_confidence = confidence
        self.category_source = "manual"

    def validate_category_assignment(self) -> Dict[str, any]:
        """Validate the current category assignment"""
        if self.category is None:
            return {
                "valid": False,
                "reason": "no_category_assigned",
                "confidence": 0.0,
                "recommendations": ["Assign category manually or provide food_group_id"]
            }
        
        if self.food_group_id is not None:
            try:
                from ..utils.food_group_mapper import FoodGroupMapper
                
                calculated_category = FoodGroupMapper.get_category(
                    self.food_group_id, self.food_name
                )
                
                if calculated_category != self.category:
                    return {
                        "valid": False,
                        "reason": "category_mismatch",
                        "assigned_category": self.category.value,
                        "calculated_category": calculated_category.value,
                        "confidence": self.category_confidence * 0.5,
                        "recommendations": [
                            f"Consider changing category from {self.category.value} to {calculated_category.value}"
                        ]
                    }
                
                return {
                    "valid": True,
                    "reason": "category_matches_calculation",
                    "confidence": self.category_confidence,
                    "recommendations": []
                }
                
            except Exception as e:
                return {
                    "valid": False,
                    "reason": f"validation_error: {str(e)}",
                    "confidence": self.category_confidence * 0.7,
                    "recommendations": ["Check food_group_id and food_name validity"]
                }
        
        # If no food_group_id, we can't validate against calculated category
        return {
            "valid": self.category_confidence > 0.5,
            "reason": "no_validation_possible_without_food_group_id",
            "confidence": self.category_confidence,
            "recommendations": ["Provide food_group_id for automatic validation"]
        }

    def get_category_info(self) -> Dict[str, any]:
        """Get detailed information about category assignment"""
        return {
            "food_id": self.food_id,
            "food_name": self.food_name,
            "food_group_id": self.food_group_id,
            "assigned_category": self.category.value if self.category else None,
            "category_confidence": self.category_confidence,
            "category_source": self.category_source,
            "validation": self.validate_category_assignment()
        }

    def __repr__(self):
        category_info = f"{self.category.value}" if self.category else "None"
        if self.category_confidence < 0.8:
            category_info += f" (conf: {self.category_confidence:.1f})"
        
        return (f"Food(ID: {self.food_id}, Name: {self.food_name}, "
                f"Category: {category_info}, Serving Size: {self.serving_size}g)")