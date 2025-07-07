from .config import MINUTES_PER_DALY

class MinutesConverter:
    @staticmethod
    def dalys_to_minutes(dalys: float) -> float:
        return dalys * MINUTES_PER_DALY