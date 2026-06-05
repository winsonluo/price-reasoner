from datetime import date, timedelta
from price_reasoner.timeseries import TimeSeriesDecomposer

def test_prophet_decompose():
    decomposer = TimeSeriesDecomposer()
    data = []
    base_date = date(2023, 1, 1)
    for i in range(30):
        d = base_date + timedelta(days=i)
        data.append({"ds": d.isoformat(), "y": 100.0 + i * 0.5 + (i % 7) * 2})

    result = decomposer.decompose(data)
    assert "trend" in result
    assert "dates" in result
    assert len(result["trend"]) == 30

def test_extract_residual():
    decomposer = TimeSeriesDecomposer()
    data = [{"ds": "2023-01-01", "y": 100}, {"ds": "2023-01-02", "y": 101}]
    residual = decomposer.extract_residual_with_dates(data)
    assert residual[0]["date"] == "2023-01-01"
    assert "residual" in residual[0]