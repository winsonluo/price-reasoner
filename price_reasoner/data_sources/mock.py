from datetime import date
from price_reasoner.data_sources.base import DataSource
from price_reasoner.models import PriceStage

class MockDataSource(DataSource):
    """Mock data source for development testing"""

    def get_price_stages(self, commodity: str, start: date, end: date) -> list[PriceStage]:
        return [
            PriceStage(
                stage_id=1,
                start_date=start,
                end_date=date(start.year, start.month + 3, 1) if start.month <= 9 else date(start.year + 1, 1, 1),
                start_price=100.0,
                end_price=115.0,
                change_pct=15.0,
                trend="上涨"
            ),
            PriceStage(
                stage_id=2,
                start_date=date(start.year, start.month + 4, 1),
                end_date=date(start.year, start.month + 7, 1),
                start_price=115.0,
                end_price=108.0,
                change_pct=-6.1,
                trend="下跌"
            ),
            PriceStage(
                stage_id=3,
                start_date=date(start.year, start.month + 8, 1),
                end_date=end,
                start_price=108.0,
                end_price=112.0,
                change_pct=3.7,
                trend="震荡"
            ),
        ]

    def get_macro_factors(self, commodity: str, start: date, end: date) -> dict:
        return {
            "美元指数": {"trend": "走强", "change": "+5%"},
            "标普500": {"trend": "震荡", "change": "+2%"},
            "10年期国债收益率": {"trend": "上行", "change": "+30bp"},
        }

    def get_event_timeline(self, commodity: str, start: date, end: date) -> list[dict]:
        return [
            {"date": f"{start.year}-03-15", "event": "某国宣布增产计划"},
            {"date": f"{start.year}-06-01", "event": "政策补贴缩减"},
            {"date": f"{start.year}-09-20", "event": "库存意外下降"},
        ]