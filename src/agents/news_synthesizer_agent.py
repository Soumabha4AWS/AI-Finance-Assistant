from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def news_synthesizer_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nested LangGraph for News Synthesizer routing between API, RAG, and BOTH (synthesis)."""
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
    from rag.news_synthesizer_rag_agent import news_synthesizer_rag_node
    from api.news_synthesizer_api_tool_call_agent import news_synthesizer_api_node

    def news_synthesizer_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Strict LLM combine: may reformat, must not invent beyond RAG/API inputs."""
        rag = news_synthesizer_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = news_synthesizer_api_node({"user_input": s.get("user_input", "")}).get("response", "")
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

    def news_synthesizer_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for requests to get today's/breaking/latest/headlines; 'RAG' for educational context; "
                    "'BOTH' when both appear. Reply only API, RAG, or BOTH."
                )
                res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=q)])
                raw = (res.content or "").strip().upper()
                if raw in ("API", "RAG", "BOTH"):
                    decision = raw
            except Exception:
                raw = ""
        ql = q.lower()
        recency_cues = (
            "headline", "headlines", "breaking", "today", "latest", "update", "announcement",
            "this morning", "this afternoon", "this evening", "pre-market", "premarket", "after hours",
            "pre market", "after-hours", "this week", "this month", "earnings", "fed", "cpi", "jobs report", "rate decision"
        )
        edu_cues = ("explain", "difference", "define", "how does", "how to", "why", "meaning", "mean", "what does", "concept", "guide")
        has_live = any(w in ql for w in recency_cues)
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
        # Pass through user_input so downstream nodes can use it
        return {"route": decision, "user_input": q}

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    news_synthesizer_graph = StateGraph(dict)
    news_synthesizer_graph.add_node("router", news_synthesizer_router_node)
    news_synthesizer_graph.add_node("api", news_synthesizer_api_node)
    news_synthesizer_graph.add_node("rag", news_synthesizer_rag_node)
    news_synthesizer_graph.add_node("synthesis", news_synthesizer_synthesis_node)
    news_synthesizer_graph.add_edge(START, "router")
    news_synthesizer_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    news_synthesizer_graph.add_edge("api", END)
    news_synthesizer_graph.add_edge("rag", END)
    news_synthesizer_graph.add_edge("synthesis", END)

    news_synthesizer_app = news_synthesizer_graph.compile()

    # Pre-extract tickers to pass as a hint to the API branch
    ui = state.get("user_input", "")
    import re as _re
    _tickers = []
    for _m in _re.findall(r"\(([A-Za-z0-9.\-]{1,6})\)", ui):
        _tickers.append(_m.upper())
    for _tok in _re.findall(r"\b[A-Z]{1,6}\b", ui):
        if _tok.upper() not in _tickers:
            _tickers.append(_tok.upper())
    tickers_hint = ",".join(_tickers) if _tickers else ""

    news_synthesizer_output = news_synthesizer_app.invoke({"user_input": ui, "tickers": tickers_hint})
    return {"response": news_synthesizer_output.get("response", "")}
