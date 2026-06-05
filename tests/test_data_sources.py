from datetime import date
from price_reasoner.data_sources.mock import MockDataSource

def test_mock_data_source_stages():
    ds = MockDataSource()
    stages = ds.get_price_stages("原油", date(2023,1,1), date(2024,1,1))
    assert len(stages) == 3
    assert stages[0].trend == "上涨"

def test_mock_data_source_events():
    ds = MockDataSource()
    events = ds.get_event_timeline("原油", date(2023,1,1), date(2024,1,1))
    assert len(events) > 0
    assert "date" in events[0]