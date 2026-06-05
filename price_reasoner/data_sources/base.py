from abc import ABC, abstractmethod
from datetime import date
from price_reasoner.models import PriceStage

class DataSource(ABC):
    @abstractmethod
    def get_price_stages(self, commodity: str, start: date, end: date) -> list[PriceStage]:
        pass

    @abstractmethod
    def get_macro_factors(self, commodity: str, start: date, end: date) -> dict:
        pass

    @abstractmethod
    def get_event_timeline(self, commodity: str, start: date, end: date) -> list[dict]:
        pass