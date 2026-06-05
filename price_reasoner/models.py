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