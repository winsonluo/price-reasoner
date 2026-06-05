from datetime import date
from price_reasoner.models import PriceStage, Factor, StageAttribution, AnalysisReport
from price_reasoner.report import ReportGenerator

def test_report_generator():
    stages = [
        PriceStage(1, date(2023,1,1), date(2023,6,30), 100, 120, 20.0, "上涨"),
    ]
    factors = [Factor(name="供给收缩", category="供需", weight=0.8, description="OPEC减产")]
    attributions = [
        StageAttribution(1, factors, "供给收缩→价格上涨", "供给端主导上涨")
    ]
    report = AnalysisReport(
        commodity="原油",
        start_date=date(2023,1,1),
        end_date=date(2023,12,31),
        stages=stages,
        attributions=attributions,
        causal_graph="供给收缩 → 价格上行 → 下游承压",
        scenarios=["乐观：库存持续低位，价格突破130"],
    )
    gen = ReportGenerator(output_dir="/tmp/test_outputs")
    path = gen.save(report, "test_report.md")
    content = path.read_text()
    assert "原油" in content
    assert "供给收缩" in content