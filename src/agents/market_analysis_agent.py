from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def market_analysis_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nested LangGraph for Market Analysis routing between API, RAG, and BOTH (synthesis)."""
    from langgraph.graph import StateGraph, START, END
    from utils.helper_reusable_items import get_openai_model

    # Optional LLM router; heuristic fallback if missing
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        llm: Any = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    except Exception:
        llm = None

    # Import external leaves
    from rag.market_analysis_rag_agent import market_analysis_rag_node
    from api.market_analysis_api_mcp_client_call_agent import market_analysis_api_node

    def market_analysis_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Strict LLM combine: may reformat, must not invent beyond RAG/API inputs."""
        rag = market_analysis_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = market_analysis_api_node({"user_input": s.get("user_input", "")}).get("response", "")
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
                f"User question (for context, do NOT answer beyond given content):\n{s.get('user_input','')}\n\n"
                f"RAG context:\n{rag}\n\nAPI data:\n{api}\n"
            )
            res = synth_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_payload)])
            content = (res.content or "").strip()
            if not content:
                content = f"[Synthesis]\nRAG: {rag}\nAPI: {api}"
            return {"response": content}
        except Exception:
            return {"response": f"[Synthesis]\nRAG: {rag}\nAPI: {api}"}

    def market_analysis_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for live/ticker/price/quote/index today queries; 'RAG' for conceptual education; "
                    "'BOTH' when both appear. Reply only API, RAG, or BOTH."
                )
                res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=q)])
                raw = (res.content or "").strip().upper()
                if raw in ("API", "RAG", "BOTH"):
                    decision = raw
            except Exception:
                raw = ""
        ql = q.lower()
        live_cues = (
            "price", "quote", "today", "live", "ticker", "intraday", "open", "close", "high", "low",
            "volume", "sp500", "s&p 500", "nasdaq", "dow", "nifty", "sensex"
        )
        edu_cues = ("explain", "difference", "define", "how does", "how to", "why", "meaning", "mean", "what does", "concept", "guide")
        has_live = any(w in ql for w in live_cues)
        has_edu_core = any(w in ql for w in edu_cues)
        what_is_present = "what is" in ql
        has_edu = has_edu_core or (what_is_present and not has_live)
        if decision is None:
            if has_live and has_edu:
                decision = "BOTH"
            elif has_live:
                decision = "API"
            elif has_edu:
                decision = "RAG"
            else:
                decision = "RAG"
        print(f"--- SUB-ROUTER: Model='{raw}' -> Selected [{decision}] ---")
        # Pass through user_input so downstream nodes always see it
        return {"route": decision, "user_input": q}

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    market_analysis_graph = StateGraph(dict)
    market_analysis_graph.add_node("router", market_analysis_router_node)
    market_analysis_graph.add_node("api", market_analysis_api_node)
    market_analysis_graph.add_node("rag", market_analysis_rag_node)
    market_analysis_graph.add_node("synthesis", market_analysis_synthesis_node)
    market_analysis_graph.add_edge(START, "router")
    market_analysis_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    market_analysis_graph.add_edge("api", END)
    market_analysis_graph.add_edge("rag", END)
    market_analysis_graph.add_edge("synthesis", END)

    market_analysis_app = market_analysis_graph.compile()

    # Provide user_input and a pre-extracted ticker hint to the inner graph
    ui = state.get("user_input", "")
    # Simple local extraction to improve robustness
    import re as _re
    _m = _re.search(r"\(([A-Za-z0-9.\-]{1,6})\)", ui)
    _sym = _m.group(1).upper() if _m else None
    if not _sym:
        _caps = _re.findall(r"\b[A-Z]{1,6}\b", ui)
        _stop = {"ETF","USD","NAV","PE","P","EPS","AI","IPO","CEO","USA","FII","GDP"}
        for _c in _caps:
            if _c not in _stop and len(_c) >= 2:
                _sym = _c
                break

    market_analysis_output = market_analysis_app.invoke({"user_input": ui, "ticker": _sym or ""})
    return {"response": market_analysis_output.get("response", "")}
