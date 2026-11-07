from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def finance_qa_node(state: dict[str, Any]) -> dict[str, Any]:
    """Build and run a nested LangGraph that routes between API and RAG.

    Everything (router, nodes, and graph wiring) is encapsulated inside this
    function to avoid module-level side effects.
    """
    # Local imports to keep the module lightweight and avoid global side effects
    from langgraph.graph import StateGraph, START, END
    import re
    from utils.helper_reusable_items import get_openai_model

    # Optional LLM router; fallback to keyword heuristic if unavailable
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        llm: Any = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    except Exception:
        llm = None

    # --- Import external nodes ---
    from rag.finance_qa_rag_agent import finance_qa_rag_node
    from api.finance_qa_api_mcp_client_call_agent import finance_qa_api_node

    def finance_qa_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Strict LLM combine: may reformat, must not invent beyond RAG/API inputs."""
        rag = finance_qa_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = finance_qa_api_node({"user_input": s.get("user_input", "")}).get("response", "")
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

    def finance_qa_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for live/market/ticker/price/quote/today queries; 'RAG' for concepts/definitions; "
                    "'BOTH' when the question mixes conceptual explanation with live data needs. "
                    "Reply with only API, RAG, or BOTH."
                )
                res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=q)])
                raw = (res.content or "").strip().upper()
                if raw in ("API", "RAG", "BOTH"):
                    decision = raw
            except Exception:
                raw = ""
        # Heuristic fallback when LLM didn't set a route
        ql = q.lower()
        live_cues = ("stock", "price", "quote", "ticker", "today", "live", "market")
        # Detect explicit ticker like (AAPL) or ALLCAPS as a live signal
        ticker_match = re.search(r"\(([A-Za-z0-9.\-]{1,6})\)", q)
        has_ticker = bool(ticker_match) or bool(re.findall(r"\b[A-Z]{1,6}\b", q))
        has_live = any(w in ql for w in live_cues) or has_ticker
        # Stricter educational cues (exclude generic "what is" unless non-live)
        edu_cues_strict = ("explain", "difference", "define", "how does", "how to", "why", "meaning", "mean", "what does", "concept", "guide")
        has_edu_core = any(w in ql for w in edu_cues_strict)
        what_is_present = "what is" in ql
        what_is_counts_as_edu = what_is_present and not has_live
        has_edu_strict = has_edu_core or what_is_counts_as_edu
        if decision is None:
            if has_live and has_edu_strict:
                decision = "BOTH"
            elif has_live:
                decision = "API"
            elif has_edu_strict:
                decision = "RAG"
            else:
                decision = "RAG"
        print(f"--- SUB-ROUTER: Model='{raw}' -> Selected [{decision}] ---")
        # Include user_input pass-through for downstream nodes
        out = {"route": decision, "user_input": q}
        # Attach normalized ticker if present
        if ticker_match:
            out["ticker"] = ticker_match.group(1).upper()
        return out

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    # --- Wire inner graph ---
    finance_qa_graph = StateGraph(dict)
    finance_qa_graph.add_node("router", finance_qa_router_node)
    finance_qa_graph.add_node("api", finance_qa_api_node)
    finance_qa_graph.add_node("rag", finance_qa_rag_node)
    finance_qa_graph.add_node("synthesis", finance_qa_synthesis_node)

    finance_qa_graph.add_edge(START, "router")
    finance_qa_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    finance_qa_graph.add_edge("api", END)
    finance_qa_graph.add_edge("rag", END)
    finance_qa_graph.add_edge("synthesis", END)

    finance_qa_graph_app = finance_qa_graph.compile()

    # Pre-extract ticker to pass as hint to API path
    ui = state.get("user_input", "")
    tm = re.search(r"\(([A-Za-z0-9.\-]{1,6})\)", ui)
    tick = tm.group(1).upper() if tm else ""

    finance_qa_graph_output = finance_qa_graph_app.invoke({"user_input": ui, "ticker": tick})
    return {"response": finance_qa_graph_output.get("response", "")}
