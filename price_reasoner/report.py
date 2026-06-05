from price_reasoner.models import AnalysisReport
from pathlib import Path

class ReportGenerator:
    """Markdown report generator"""

    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, report: AnalysisReport) -> str:
        lines = [
            f"# {report.commodity} 价格走势 AI 归因分析报告",
            "",
            f"**分析时间范围：** {report.start_date} ~ {report.end_date}",
            "",
            "---",
            "",
            "## 一、价格阶段划分",
            "",
            "| 阶段 | 时间范围 | 起始价格 | 终止价格 | 涨跌幅 | 趋势 |",
            "|------|----------|----------|----------|--------|------|",
        ]
        for s in report.stages:
            lines.append(
                f"| 阶段{s.stage_id} | {s.start_date} ~ {s.end_date} | "
                f"{s.start_price} | {s.end_price} | {s.change_pct:+.1f}% | {s.trend} |"
            )

        lines += ["", "## 二、各阶段归因分析", ""]
        for attr in report.attributions:
            lines.append(f"### 阶段 {attr.stage_id}：{attr.ai_reasoning}")
            lines.append("")
            lines.append("**核心驱动因子：**")
            lines.append("")
            lines.append("| 因子 | 类别 | 权重 | 说明 |")
            lines.append("|------|------|------|------|")
            for f in attr.top_factors:
                lines.append(f"| {f.name} | {f.category} | {f.weight:.2f} | {f.description} |")
            lines += ["", f"**因果链：** {attr.causal_chain}", "", "---", ""]

        lines += ["", "## 三、全局因果图", "", report.causal_graph, "", "---", ""]
        lines += ["", "## 四、情景模拟", ""]
        for i, s in enumerate(report.scenarios, 1):
            lines.append(f"**情景{i}：** {s}")

        return "\n".join(lines)

    def save(self, report: AnalysisReport, filename: str) -> Path:
        content = self.generate(report)
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        return path