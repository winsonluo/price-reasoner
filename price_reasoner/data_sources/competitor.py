from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from price_reasoner.models import (
    CompetitorData,
    CompetitorSpec,
    CompetitorPricePoint,
    CompetitorProduct,
)


class CompetitorDataSource(ABC):
    """Data source for competitor information."""

    @abstractmethod
    def list_competitors(self, commodity: str) -> list[str]:
        """Return known competitor names for this commodity."""
        pass

    @abstractmethod
    def get_competitor_data(
        self, competitor: str, start: date, end: date
    ) -> Optional[CompetitorData]:
        """Fetch competitor data for the given period."""
        pass

    @abstractmethod
    def generate_collection_plan(
        self, commodity: str, target_competitors: list[str]
    ) -> list[CompetitorSpec]:
        """
        Given a commodity and list of competitors, generate a data
        collection plan: specify what dimensions to collect for each
        competitor and why they matter for this particular product.
        """
        pass
