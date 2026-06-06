from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class PriceStage(BaseModel):
    """Price stage definition"""
    stage_id: int
    start_date: date
    end_date: date
    start_price: float
    end_price: float
    change_pct: float
    trend: str  # "上涨" / "下跌" / "震荡"

class Factor(BaseModel):
    """Driving factor"""
    name: str
    category: str  # 供需/政策/金融/情绪/替代品/外生/市场结构/产业链
    weight: float = Field(ge=0, le=1, description="Weight 0~1")
    description: str = ""

class StageAttribution(BaseModel):
    """Stage attribution result"""
    stage_id: int
    top_factors: list[Factor]
    causal_chain: str
    ai_reasoning: str

class AnalysisReport(BaseModel):
    """Full analysis report"""
    commodity: str
    start_date: date
    end_date: date
    stages: list[PriceStage]
    attributions: list[StageAttribution]
    causal_graph: str
    scenarios: list[str]


# ── Competitor Analysis ──────────────────────────────────────────────────────

class CompetitorSpec(BaseModel):
    """Specification for what competitor data to collect."""
    competitor_name: str
    data_dimensions: list[str]  # e.g. ["price_history", "market_share", "product_features"]
    start_date: date
    end_date: date
    notes: str = ""


class CompetitorPricePoint(BaseModel):
    """Single price data point for a competitor."""
    date: date
    price: float
    currency: str = "CNY"
    source: str = ""


class CompetitorProduct(BaseModel):
    """A product/sub-product from a competitor."""
    name: str
    launch_date: Optional[date] = None
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    key_features: list[str] = []
    target_segment: str = ""  # 高端/中端/低端


class CompetitorData(BaseModel):
    """Complete competitor dataset."""
    competitor_name: str
    price_history: list[CompetitorPricePoint] = []
    market_share_pct: Optional[float] = None
    products: list[CompetitorProduct] = []
    channel_info: dict[str, str] = {}  # e.g. {"线上": "天猫/京东", "线下": "专柜"}
    brand_sentiment: Optional[dict] = None  # e.g. {"positive": 0.7, "negative": 0.2, "neutral": 0.1}
    promotions: list[str] = []  # major promotions in the period
    metadata: dict = {}


class CompetitorReport(BaseModel):
    """Full competitor analysis report."""
    target_commodity: str
    competitors: list[CompetitorData]
    data_collection_plan: list[CompetitorSpec]  # what to collect and why
    competitive_matrix: dict  # e.g. {"price": {...}, "features": {...}}
    insights: list[str]  # AI-generated insights
    gaps: list[str]  # data gaps / areas needing further research