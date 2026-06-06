from datetime import date, timedelta
from price_reasoner.data_sources.competitor import CompetitorDataSource
from price_reasoner.models import (
    CompetitorData,
    CompetitorSpec,
    CompetitorPricePoint,
    CompetitorProduct,
)


class MockCompetitorDataSource(CompetitorDataSource):
    """Mock competitor source for development."""

    # 通用竞品数据库（实际项目可替换为 API / 爬虫 / 数据库）
    _CATALOG = {
        "Dior S8U 墨镜": [
            {
                "name": "Gucci GG0764 墨镜",
                "segment": "高端",
                "price_range": (4500, 6000),
                "features": ["矩形框架", "金属腿", "UV400防护"],
                "channels": {"线上": "天猫国际", "线下": "专柜"},
            },
            {
                "name": "Prada PR01WS 墨镜",
                "segment": "高端",
                "price_range": (3800, 5200),
                "features": ["复古风格", "醋酸纤维", "偏光镜片"],
                "channels": {"线上": "京东", "线下": "专柜"},
            },
            {
                "name": "Celine CL40019 墨镜",
                "segment": "高端",
                "price_range": (4000, 5500),
                "features": ["简约设计", "轻量板材", "中性款"],
                "channels": {"线上": "天猫国际", "线下": "买手店"},
            },
        ],
    }

    def list_competitors(self, commodity: str) -> list[str]:
        cats = self._CATALOG.get(commodity, [])
        return [c["name"] for c in cats]

    def get_competitor_data(
        self, competitor: str, start: date, end: date
    ):
        """Generate realistic mock competitor data."""
        # Find in catalog
        catalog_entry = None
        for cats in self._CATALOG.values():
            for c in cats:
                if c["name"] == competitor:
                    catalog_entry = c
                    break

        # Generate price history (monthly points)
        if catalog_entry:
            low, high = catalog_entry["price_range"]
            base_price = (low + high) / 2
        else:
            base_price = 4000.0
            catalog_entry = {
                "name": competitor,
                "segment": "未知",
                "price_range": (3500, 5000),
                "features": [],
                "channels": {"线上": "未知", "线下": "未知"},
            }

        price_history = []
        current_date = start
        price = base_price
        import random
        random.seed(hash(competitor) % 2**32)
        while current_date <= end:
            price_history.append(
                CompetitorPricePoint(
                    date=current_date,
                    price=round(price, 2),
                    currency="CNY",
                    source="mock",
                )
            )
            price = price * (1 + random.uniform(-0.03, 0.04))
            # Move ~30 days forward
            current_date += timedelta(days=30)

        return CompetitorData(
            competitor_name=competitor,
            price_history=price_history,
            market_share_pct=round(random.uniform(5, 25), 1),
            products=[
                CompetitorProduct(
                    name=catalog_entry["name"],
                    price_range_low=catalog_entry["price_range"][0],
                    price_range_high=catalog_entry["price_range"][1],
                    key_features=catalog_entry["features"],
                    target_segment=catalog_entry["segment"],
                )
            ],
            channel_info=catalog_entry["channels"],
            brand_sentiment={"positive": round(random.uniform(0.6, 0.85), 2),
                             "negative": round(random.uniform(0.05, 0.15), 2),
                             "neutral": round(random.uniform(0.05, 0.20), 2)},
            promotions=["618预售", "双十一满减"],
        )

    def generate_collection_plan(
        self, commodity: str, target_competitors: list[str]
    ) -> list[CompetitorSpec]:
        """Use AI to generate a tailored data collection plan."""
        # Return a template plan; caller can refine with AI
        dimension_library = {
            "price_history": "历史价格走势，用于对比定价策略",
            "market_share": "市场份额，了解竞争格局",
            "product_features": "产品规格参数，对比产品力",
            "channel_strategy": "渠道布局，了解销售网络",
            "promotion_activities": "促销活动，识别促销节奏",
            "brand_sentiment": "品牌舆情，了解消费者态度",
            "new_product_launch": "新品发布，识别产品迭代",
        }

        plan = []
        for comp in target_competitors:
            plan.append(
                CompetitorSpec(
                    competitor_name=comp,
                    data_dimensions=[
                        "price_history",
                        "product_features",
                        "channel_strategy",
                        "promotion_activities",
                        "brand_sentiment",
                    ],
                    start_date=date.today(),
                    end_date=date.today(),
                    notes="需重点关注定价区间与目标商品的差异",
                )
            )
        return plan
