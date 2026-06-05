from price_reasoner.ai_reasoner import AIReasoner

def test_ai_reasoner_init():
    reasoner = AIReasoner()
    assert reasoner.llm is not None