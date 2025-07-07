from dataclasses import dataclass, field
from typing import Dict
from ..database.cnf_database import CNFDatabase

@dataclass
class Ingredient:
    food_id: int
    amount: float
    unit: str
    cnf_db: CNFDatabase
    kcal: float = 0.0
    dietary_risks: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.food_id = int(self.food_id)
        self.amount = float(self.amount)
        self.kcal = float(self.cnf_db.get_kcal(self.food_id))
        self.dietary_risks = self.cnf_db.get_dietary_risks(self.food_id)