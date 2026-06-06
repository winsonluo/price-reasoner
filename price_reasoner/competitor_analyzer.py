"""
Competitor Analysis Module.

Responsibilities:
1. Decide which competitors to track for a given product
2. Generate a data collection plan (what dimensions, why)
3. Analyze collected data and produce insights
"""

import json
from datetime import date
from price_reasoner.ai_reasoner import AIReasoner
from price_reasoner.config import Config
from price_reasoner.models import (
    CompetitorData,
    CompetitorReport,
    CompetitorSpec,
    CompetitorPricePoint,
)


class CompetitorAnalyzer:
    """AI-driven competitor analysis."""

    # All possible data dimensions with explanations
    DIMENSION_LIBRARY = {
        "price_history": "历史价格走势，用于对比定价策略和促销节奏",
        "market_share": "市场份额，了解整体竞争格局",
        "product_features": "产品规格参数，对比产品力差异",
        "channel_strategy": "线上/线下渠道布局，了解销售网络覆盖",
        "promotion_activities": "促销活动，识别促销强度和节奏",
        "brand_sentiment": "品牌舆情，了解消费者态度和口碑",
        "new_product_launch": "新品发布，识别产品迭代周期",
        "pricing_tiers": "价格分层（高中低端），识别市场定位差异",
        "user_reviews": "用户评论关键词，识别真实痛点和需求",
        "inventory_pressure": "库存压力，判断是否存在价格战风险",
    }

    def __init__(self):
        self.llm = AIReasoner().llm
        self.config = Config()

    def recommend_competitors(self, commodity: str) -> list[dict]:
        """
        Given a commodity, use AI to recommend who to track and why.
        Returns a list of dicts with competitor name + selection rationale.
        """
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template(
            """You are a market analyst. For the product category below, recommend the top 5 competitors to track.

Product: {commodity}

For each competitor, provide:
1. Competitor brand name (in Chinese if applicable)
2. Why they are a key competitor (1 sentence)
3. Which data dimensions matter most for this specific competitor

Output JSON array:
[
  {{
    "name": "competitor name",
    "rationale": "why this is a key competitor",
    "priority_dimensions": ["price_history", "product_features", ...]
  }}
]

Consider: direct rivals, aspirational benchmarks, emerging players."""
        )

        chain = prompt | self.llm
        result = chain.invoke({"commodity": commodity})
        content = result.content
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)

    def generate_collection_plan(
        self,
        commodity: str,
        target_competitors: list[dict],
        current_product_info: dict,
    ) -> list[CompetitorSpec]:
        """
        Generate a tailored data collection plan for each competitor.

        current_product_info: e.g. {
          "name": "Dior S8U",
          "price_range": "4000-6000",
          "target_segment": "高端",
          "key_features": ["醋酸纤维", "54mm镜片"],
          "channels": ["线上天猫", "线下专柜"]
        }
        """
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template(
            """You are a research strategist. Create a data collection plan for competitor analysis.

Target Product: {commodity}
Product Info: {current_product_info}

Competitors to analyze:
{competitors_json}

For EACH competitor, specify:
1. Which data dimensions to collect (choose from the library)
2. Why each dimension matters for THIS competitor specifically
3. Data collection priority: HIGH / MEDIUM / LOW
4. Any special notes or warnings about data quality

Dimension library (only use dimensions from this list):
{dimension_library}

Output JSON array:
[
  {{
    "competitor_name": "...",
    "data_dimensions": [
      {{
        "dimension": "price_history",
        "priority": "HIGH/MEDIUM/LOW",
        "rationale": "why this matters for this competitor"
      }}
    ],
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "notes": "special considerations"
  }}
]

Today is {today}. Cover at least the last 12 months.""".format(
                today=date.today().isoformat(),
                dimension_library=json.dumps(self.DIMENSION_LIBRARY, ensure_ascii=False, indent=2),
            )
        )

        chain = prompt | self.llm
        competitors_str = json.dumps(target_competitors, ensure_ascii=False, indent=2)
        product_info_str = json.dumps(current_product_info, ensure_ascii=False, indent=2)

        result = chain.invoke({
            "commodity": commodity,
            "current_product_info": product_info_str,
            "competitors_json": competitors_str,
        })

        content = result.content
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()
        parsed = json.loads(content)

        specs = []
        today = date.today()
        for item in parsed:
            dims = [d["dimension"] for d in item.get("data_dimensions", [])]
            specs.append(
                CompetitorSpec(
                    competitor_name=item["competitor_name"],
                    data_dimensions=dims,
                    start_date=today.replace(year=today.year - 1),
                    end_date=today,
                    notes=item.get("notes", ""),
                )
            )
        return specs

    def build_competitive_matrix(
        self,
        commodity: str,
        competitors: list[CompetitorData],
        current_product: dict,
    ) -> dict:
        """
        From collected competitor data, build a multi-dimensional comparison matrix.
        """
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template(
            """You are a competitive intelligence analyst. Build a structured comparison matrix.

Target Product: {commodity}
My Product: {current_product}

Competitor Data:
{competitors_json}

Generate a structured competitive matrix with the following dimensions:
1. Price positioning (who is higher/lower vs target)
2. Product features comparison
3. Channel coverage
4. Promotion intensity
5. Brand sentiment comparison
6. Market share ranking

Also identify:
- Key gaps in our product vs competitors
- Overlap zones (direct competition)
- Differentiating opportunities

Output a detailed JSON object."""
        )

        chain = prompt | self.llm
        competitors_data = [
            {
                "name": c.competitor_name,
                "price_range": (
                    f"{c.products[0].price_range_low}-{c.products[0].price_range_high}"
                    if c.products and c.products[0].price_range_low
                    else "N/A"
                ),
                "market_share": c.market_share_pct,
                "channels": c.channel_info,
                "sentiment": c.brand_sentiment,
                "promotions": c.promotions,
            }
            for c in competitors
        ]
        result = chain.invoke({
            "commodity": commodity,
            "current_product": json.dumps(current_product, ensure_ascii=False),
            "competitors_json": json.dumps(competitors_data, ensure_ascii=False, indent=2),
        })

        content = result.content
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)

    def generate_insights(
        self,
        commodity: str,
        competitors: list[CompetitorData],
        matrix: dict,
        gaps: list[str],
    ) -> list[str]:
        """
        From the matrix and gaps, generate actionable insights.
        """
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template(
            """You are a senior market strategist. Generate actionable insights from this competitive analysis.

Product: {commodity}

Competitive Matrix Summary:
{matrix}

Data Gaps (areas needing more research):
{gaps}

Generate 5-8 concise, actionable insights that:
1. Highlight key competitive advantages to exploit
2. Warn about threats or risks
3. Suggest positioning adjustments
4. Identify untapped opportunities

Each insight 1-2 sentences. Be specific, not generic."""
        )

        chain = prompt | self.llm
        result = chain.invoke({
            "commodity": commodity,
            "matrix": json.dumps(matrix, ensure_ascii=False, indent=2),
            "gaps": "\n".join(f"- {g}" for g in gaps),
        })

        return [s.strip() for s in result.content.split("\n") if s.strip() and not s.startswith("#")]

    def produce_report(
        self,
        commodity: str,
        competitors: list[CompetitorData],
        collection_plan: list[CompetitorSpec],
        current_product: dict,
    ) -> CompetitorReport:
        """Run the full competitor analysis pipeline and return a report."""
        matrix = self.build_competitive_matrix(commodity, competitors, current_product)
        gaps = [s.notes for s in collection_plan if "未" in s.notes or "?" in s.notes]
        insights = self.generate_insights(commodity, competitors, matrix, gaps)

        return CompetitorReport(
            target_commodity=commodity,
            competitors=competitors,
            data_collection_plan=collection_plan,
            competitive_matrix=matrix,
            insights=insights,
            gaps=gaps,
        )
