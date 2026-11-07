from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def portfolio_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nested LangGraph for Portfolio Analysis routing between API, RAG, and BOTH (synthesis)."""
    from langgraph.graph import StateGraph, START, END
    from utils.helper_reusable_items import get_openai_model

    # Optional LLM router; heuristic fallback if not available
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        llm: Any = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    except Exception:
        llm = None

    # Import external leaves
    from rag.portfolio_analysis_rag_agent import portfolio_analysis_rag_node
    from api.portfolio_analysis_api_mcp_client_call_agent import portfolio_analysis_api_node

    def portfolio_analysis_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Strict LLM combine: may reformat, must not invent beyond RAG/API inputs."""
        rag = portfolio_analysis_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = portfolio_analysis_api_node({"user_input": s.get("user_input", "")}).get("response", "")
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            synth_llm: Any = ChatOpenAI(model=get_openai_model(), temperature=0.0)
            system_prompt = (
                "You will be given two blocks of text: 'RAG context' and 'API data'. "
                "Your job is ONLY to combine, organize, and restyle these exact contents. "
                "STRICT RULES: Do NOT add, infer, or fabricate any new facts, numbers, dates, or guidance. "
                "Only use wording that appears in the inputs, with minimal connective phrasing allowed solely for flow (e.g., headings, bullets). "
                "If a part is empty, you may label it as 'No content'. Do not speculate or expand beyond the inputs."
            )
            user_payload = (
                f"User request (for context, do NOT answer beyond given content):\n{s.get('user_input','')}\n\n"
                f"RAG context:\n{rag}\n\nAPI data:\n{api}\n"
            )
            res = synth_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_payload)])
            content = (res.content or "").strip()
            if not content:
                content = f"[Synthesis]\nRAG: {rag}\nAPI: {api}"
            return {"response": content}
        except Exception:
            return {"response": f"[Synthesis]\nRAG: {rag}\nAPI: {api}"}

    def portfolio_analysis_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for metrics/exposure/optimization/backtest; 'RAG' for conceptual advice; "
                    "'BOTH' when both appear. Reply only API, RAG, or BOTH."
                )
                res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=q)])
                raw = (res.content or "").strip().upper()
                if raw in ("API", "RAG", "BOTH"):
                    decision = raw
            except Exception:
                raw = ""
        ql = q.lower()
        api_cues = (
            "exposure", "sector weight", "sector weights", "weights", "allocation", "rebalance now",
            "risk", "volatility", "beta", "sharpe", "returns", "performance", "drawdown", "correlation",
            "optimize", "optimization", "backtest", "back-testing", "metrics"
        )
        edu_cues = ("explain", "difference", "define", "how does", "how to", "why", "meaning", "mean", "what does", "concept", "guide")
        has_api = any(w in ql for w in api_cues)
        has_edu = any(w in ql for w in edu_cues) or ("what is" in ql and not has_api)
        if decision is None:
            if has_api and has_edu:
                decision = "BOTH"
            elif has_api:
                decision = "API"
            elif has_edu:
                decision = "RAG"
            else:
                decision = "RAG"
        print(f"--- SUB-ROUTER: Model='{raw}' -> Selected [{decision}] ---")
        # Preserve user_input so downstream API/RAG nodes can parse it
        return {"route": decision, "user_input": s.get("user_input", "")}

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    portfolio_analysis_graph = StateGraph(dict)
    portfolio_analysis_graph.add_node("router", portfolio_analysis_router_node)
    portfolio_analysis_graph.add_node("api", portfolio_analysis_api_node)
    portfolio_analysis_graph.add_node("rag", portfolio_analysis_rag_node)
    portfolio_analysis_graph.add_node("synthesis", portfolio_analysis_synthesis_node)
    portfolio_analysis_graph.add_edge(START, "router")
    portfolio_analysis_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    portfolio_analysis_graph.add_edge("api", END)
    portfolio_analysis_graph.add_edge("rag", END)
    portfolio_analysis_graph.add_edge("synthesis", END)

    portfolio_analysis_app = portfolio_analysis_graph.compile()
    portfolio_analysis_output = portfolio_analysis_app.invoke({"user_input": state.get("user_input", "")})
    return {"response": portfolio_analysis_output.get("response", "")}
