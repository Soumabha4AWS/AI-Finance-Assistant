import pytest

from workflow import aiFinanceWorkflow


def test_compiled_workflow_contains_expected_nodes():
    graph = aiFinanceWorkflow.compiled_finance_app.get_graph()
    node_names = list(graph.nodes.keys())

    assert "__start__" in node_names
    assert "router" in node_names
    assert "finance_qa" in node_names
    assert "portfolio_analysis" in node_names
    assert "market_analysis" in node_names
    assert "goal_planning" in node_names
    assert "news_synthesizer" in node_names
    assert "tax_education" in node_names
    assert "default" in node_names
    assert "__end__" in node_names

    edges = [(edge.source, edge.target, getattr(edge, "data", None)) for edge in graph.edges]
    assert ("__start__", "router", None) in edges
    assert ("router", "default", None) in edges
    assert ("router", "finance_qa", "finance qa") in edges
    assert ("router", "portfolio_analysis", "portfolio analysis") in edges
    assert ("router", "market_analysis", "market analysis") in edges
    assert ("router", "goal_planning", "goal planning") in edges
    assert ("router", "news_synthesizer", "news synthesizer") in edges
    assert ("router", "tax_education", "tax education") in edges


def test_managed_finance_app_invoke_calls_lifecycle_and_returns_output(monkeypatch):
    calls = []

    monkeypatch.setattr(aiFinanceWorkflow, "begin_workflow", lambda: calls.append("begin"))
    monkeypatch.setattr(aiFinanceWorkflow, "end_workflow", lambda: calls.append("end"))

    expected = {
        "user_input": "How much should I save for retirement?",
        "selected_agent": "goal planning",
        "response": "Monthly savings target is about $1,200.",
    }

    monkeypatch.setattr(aiFinanceWorkflow.compiled_finance_app, "invoke", lambda *args, **kwargs: expected)

    result = aiFinanceWorkflow.financeApp.invoke({"user_input": expected["user_input"], "selected_agent": "", "response": ""})

    assert result == expected
    assert calls == ["begin", "end"]


@pytest.mark.asyncio
async def test_managed_finance_app_ainvoke_calls_lifecycle_and_returns_output(monkeypatch):
    calls = []

    def fake_begin():
        calls.append("begin")

    def fake_end():
        calls.append("end")

    expected = {
        "user_input": "What is a diversified portfolio?",
        "selected_agent": "finance qa",
        "response": "A diversified portfolio spreads risk across asset classes.",
    }

    async def fake_ainvoke(*args, **kwargs):
        return expected

    monkeypatch.setattr(aiFinanceWorkflow, "begin_workflow", fake_begin)
    monkeypatch.setattr(aiFinanceWorkflow, "end_workflow", fake_end)
    monkeypatch.setattr(aiFinanceWorkflow.compiled_finance_app, "ainvoke", fake_ainvoke)

    result = await aiFinanceWorkflow.financeApp.ainvoke({"user_input": expected["user_input"], "selected_agent": "", "response": ""})

    assert result == expected
    assert calls == ["begin", "end"]
