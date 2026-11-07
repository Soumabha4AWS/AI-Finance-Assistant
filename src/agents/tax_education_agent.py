from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def tax_education_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nested LangGraph for Tax Education routing between API and RAG.

    Decides whether the user needs up-to-date figures (rates/limits/deadlines)
    or conceptual guidance (definitions, differences, how-tos).
    """
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
    from rag.tax_education_rag_agent import tax_education_rag_node
    from api.tax_education_api_tool_call_agent import tax_education_api_node

    def tax_education_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Combine RAG and API outputs using an LLM that must not invent content.

        The LLM may rephrase/format for clarity, but it MUST only use the
        provided RAG/API texts. No new data, claims, or numbers are allowed.
        """
        rag = tax_education_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = tax_education_api_node({"user_input": s.get("user_input", "")}).get("response", "")
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

    def tax_education_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for current-year limits/thresholds/brackets/rates/deadlines; 'RAG' for education; "
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
            "today", "latest", "current", "this year", "fy", "ay", "deadline", "due date", "last date",
            "limit", "threshold", "bracket", "slab", "rate", "rebate", "surcharge", "section 80c", "80c",
            "80d", "hsa", "ira", "pf", "pension contribution"
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
        return {"route": decision}

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    tax_education_graph = StateGraph(dict)
    tax_education_graph.add_node("router", tax_education_router_node)
    tax_education_graph.add_node("api", tax_education_api_node)
    tax_education_graph.add_node("rag", tax_education_rag_node)
    tax_education_graph.add_node("synthesis", tax_education_synthesis_node)
    tax_education_graph.add_edge(START, "router")
    tax_education_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    tax_education_graph.add_edge("api", END)
    tax_education_graph.add_edge("rag", END)
    tax_education_graph.add_edge("synthesis", END)

    tax_education_app = tax_education_graph.compile()
    tax_education_output = tax_education_app.invoke({"user_input": state.get("user_input", "")})
    return {"response": tax_education_output.get("response", "")}
