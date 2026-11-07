import agents.router_agent as router_mod


def test_route_decision_returns_selected_agent():
    assert router_mod.route_decision({"selected_agent": "market analysis"}) == "market analysis"


def test_router_routes_market_questions(monkeypatch):
    monkeypatch.setattr(router_mod, "llm", None)
    result = router_mod.router_node({"user_input": "What is the stock trend for AAPL today?"})
    assert result["selected_agent"] == "market analysis"


def test_router_routes_portfolio_questions(monkeypatch):
    monkeypatch.setattr(router_mod, "llm", None)
    result = router_mod.router_node({"user_input": "Review my portfolio allocation and tell me if I am too tech-heavy."})
    assert result["selected_agent"] == "portfolio analysis"


def test_router_routes_goal_questions(monkeypatch):
    monkeypatch.setattr(router_mod, "llm", None)
    result = router_mod.router_node({"user_input": "How much should I save monthly to retire in 25 years with a $2 million target?"})
    assert result["selected_agent"] == "goal planning"


def test_router_routes_tax_questions(monkeypatch):
    monkeypatch.setattr(router_mod, "llm", None)
    result = router_mod.router_node({"user_input": "What are the tax advantages of a Roth IRA compared to a traditional IRA?"})
    assert result["selected_agent"] == "tax education"


def test_router_defaults_unknown_questions(monkeypatch):
    monkeypatch.setattr(router_mod, "llm", None)
    result = router_mod.router_node({"user_input": "Tell me about a random unrelated topic."})
    assert result["selected_agent"] == "default"
