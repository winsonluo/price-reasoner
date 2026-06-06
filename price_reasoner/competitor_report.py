"""
Competitor Analysis Report Generator.
Outputs a clean Markdown report from a CompetitorReport model.
"""

from pathlib import Path
from price_reasoner.models import CompetitorReport, CompetitorData


class CompetitorReportGenerator:
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, report: CompetitorReport, filename: str = "competitor_report.md") -> Path:
        path = self.output_dir / filename
        path.write_text(self._render(report), encoding="utf-8")
        return path

    def _render(self, report: CompetitorReport) -> str:
        lines = [
            f"# 竞品分析报告：{report.target_commodity}",
            "",
            "## 一、数据采集计划",
            "",
        ]

        for spec in report.data_collection_plan:
            lines.append(f"### {spec.competitor_name}")
            lines.append(f"**采集维度：** {', '.join(spec.data_dimensions)}")
            lines.append(f"**时间范围：** {spec.start_date} ~ {spec.end_date}")
            if spec.notes:
                lines.append(f"**备注：** {spec.notes}")
            lines.append("")

        lines += [
            "## 二、竞品横向对比矩阵",
            "",
            self._render_matrix(report.competitive_matrix),
            "",
            "## 三、核心洞察",
            "",
        ]
        for insight in report.insights:
            lines.append(f"- {insight}")

        if report.gaps:
            lines += ["", "## 四、数据缺口与后续研究建议", ""]
            for gap in report.gaps:
                lines.append(f"- {gap}")

        lines += ["", "## 五、竞品详情", ""]
        for comp in report.competitors:
            lines += self._render_competitor(comp)

        return "\n".join(lines)

    def _render_matrix(self, matrix: dict) -> str:
        """Render the competitive matrix as a markdown table or structured text."""
        if isinstance(matrix, dict):
            # Try to render as structured sections
            sections = []
            for key, val in matrix.items():
                sections.append(f"**{key}**：{val}")
            return "\n".join(sections) if sections else "（待 AI 生成）"
        return str(matrix)

    def _render_competitor(self, comp: CompetitorData) -> list[str]:
        lines = [
            f"### {comp.competitor_name}",
            f"- 市场份额：{comp.market_share_pct}%" if comp.market_share_pct else "- 市场份额：未知",
            f"- 品牌舆情：正面 {comp.brand_sentiment['positive']} / 负面 {comp.brand_sentiment['negative']}" if comp.brand_sentiment else "",
        ]
        if comp.products:
            for p in comp.products:
                lines.append(f"- 产品：{p.name}（{p.target_segment}）")
                lines.append(f"  价格区间：¥{p.price_range_low:,} - ¥{p.price_range_high:,}")
                if p.key_features:
                    lines.append(f"  核心特性：{', '.join(p.key_features)}")
        if comp.channel_info:
            channels = " / ".join(f"{k}: {v}" for k, v in comp.channel_info.items())
            lines.append(f"- 渠道：{channels}")
        if comp.promotions:
            lines.append(f"- 促销活动：{', '.join(comp.promotions)}")
        lines.append("")
        return lines
