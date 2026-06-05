from datetime import date
from price_reasoner.models import PriceStage, Factor, StageAttribution, AnalysisReport

def test_price_stage_model():
    stage = PriceStage(
        stage_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 6, 30),
        start_price=100.0,
        end_price=120.0,
        change_pct=20.0,
        trend="上涨"
    )
    assert stage.trend == "上涨"
    assert stage.change_pct == 20.0

def test_factor_model():
    f = Factor(name="库存下降", category="供需", weight=0.7, description="库存降至5年低位")
    assert f.weight == 0.7

def test_full_report_model():
    report = AnalysisReport(
        commodity="原油",
        start_date=date(2023, 1, 1),
        end_date=date(2024, 1, 1),
        stages=[],
        attributions=[],
        causal_graph="",
        scenarios=[]
    )
    assert report.commodity == "原油"