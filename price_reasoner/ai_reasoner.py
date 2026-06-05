import os
import json
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from price_reasoner.models import PriceStage, StageAttribution, Factor
from price_reasoner.config import Config

config = Config()

class AIReasoner:
    """AI attribution engine using LangChain + Claude"""

    def __init__(self):
        self.llm = ChatAnthropic(
            model=config.model,
            api_key=config.anthropic_api_key,
            temperature=0.3,
        )

    def analyze_stage_attribution(
        self,
        stage: PriceStage,
        macro_factors: dict,
        event_timeline: list[dict],
    ) -> StageAttribution:
        """Analyze driving factors for a single price stage"""
        prompt = PromptTemplate.from_template(
            """You are a commodity price analyst. Analyze the driving factors for this price stage.

Stage Info:
- Stage: {stage_id}
- Period: {start_date} ~ {end_date}
- Start Price: {start_price}
- End Price: {end_price}
- Change: {change_pct}%
- Trend: {trend}

Macro Factors:
{macro_factors}

Key Events:
{events}

Please identify:
1. Top 3 driving factors with weights (0~1) and descriptions
2. Causal relationships between factors
3. One-sentence summary of the core reason

Output JSON:
{{
  "top_factors": [
    {{"name": "factor name", "category": "supply_demand/policy/financial/emotion/substitute/external/market_structure/supply_chain", "weight": 0.0~1.0, "description": "description"}}
  ],
  "causal_chain": "causal chain description",
  "ai_reasoning": "one sentence summary"
}}"""
        )

        events_str = "\n".join([f"- {e['date']}: {e['event']}" for e in event_timeline])
        macro_str = "\n".join([f"- {k}: {v}" for k, v in macro_factors.items()])

        chain = prompt | self.llm
        result = chain.invoke({
            "stage_id": stage.stage_id,
            "start_date": stage.start_date.isoformat(),
            "end_date": stage.end_date.isoformat(),
            "start_price": stage.start_price,
            "end_price": stage.end_price,
            "change_pct": stage.change_pct,
            "trend": stage.trend,
            "macro_factors": macro_str,
            "events": events_str,
        })

        content = result.content
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()
        parsed = json.loads(content)

        factors = [Factor(**f) for f in parsed["top_factors"]]
        return StageAttribution(
            stage_id=stage.stage_id,
            top_factors=factors,
            causal_chain=parsed["causal_chain"],
            ai_reasoning=parsed["ai_reasoning"],
        )

    def build_causal_graph(self, attributions: list[StageAttribution]) -> str:
        """Build global causal graph from stage attributions"""
        prompt = PromptTemplate.from_template(
            """Based on the following stage attribution results, generate a global causal chain description.
            
Stages:
{attributions}

Output a text-based causal graph with arrows showing causal directions."""
        )
        chain = prompt | self.llm
        attr_text = "\n---\n".join([
            f"Stage {a.stage_id}: {a.causal_chain}" for a in attributions
        ])
        result = chain.invoke({"attributions": attr_text})
        return result.content

    def scenario_simulation(
        self,
        commodity: str,
        current_factors: dict,
        hypotheses: list[str],
    ) -> list[str]:
        """Simulate price scenarios given hypothetical conditions"""
        prompt = PromptTemplate.from_template(
            """As a commodity price analyst, simulate {commodity} price scenarios.

Current Core Factors:
{current_factors}

Hypotheses:
{hypotheses}

Generate 3 scenarios (bull/baseline/bear) with:
- Trigger conditions
- Price direction and magnitude
- Key risk factors

Each scenario 3-5 sentences."""
        )
        chain = prompt | self.llm
        factors_str = "\n".join([f"- {k}: {v}" for k, v in current_factors.items()])
        hypotheses_str = "\n".join([f"- {h}" for h in hypotheses])
        result = chain.invoke({
            "commodity": commodity,
            "current_factors": factors_str,
            "hypotheses": hypotheses_str,
        })
        return [s.strip() for s in result.content.split("\n\n") if s.strip()]