from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def goal_planning_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nested LangGraph for Goal Planning that routes between API and RAG.

    Mirrors the structure used in finance_qa_agent: a local mini-graph with a
    router and two leaf nodes (API/RAG). All wiring stays inside this function.
    """
    from langgraph.graph import StateGraph, START, END
    from utils.helper_reusable_items import get_openai_model

    # Optional LLM router; fallback to keyword heuristic if unavailable
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        llm: Any = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    except Exception:
        llm = None

    # Import external leaf nodes
    from rag.goal_planning_rag_agent import goal_planning_rag_node
    from api.goal_planning_api_tool_call_agent import goal_planning_api_node

    def goal_planning_synthesis_node(s: dict[str, Any]) -> dict[str, Any]:
        """Strict LLM combine: may reformat, must not invent beyond RAG/API inputs."""
        rag = goal_planning_rag_node({"user_input": s.get("user_input", "")}).get("response", "")
        api = goal_planning_api_node({"user_input": s.get("user_input", "")}).get("response", "")
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

    def goal_planning_router_node(s: dict[str, Any]) -> dict[str, Any]:
        q = (s.get("user_input") or "").strip()
        decision: str | None = None
        raw = ""
        if llm is not None and q:
            try:
                sys_prompt = (
                    "Decide one of: 'API', 'RAG', or 'BOTH'. "
                    "Use 'API' for numeric outputs (monthly invest, target corpus, SIP), or rates/returns/inflation/today. "
                    "Use 'RAG' for conceptual education. Use 'BOTH' when both numeric and conceptual cues are present. "
                    "Reply only API, RAG, or BOTH."
                )
                res = llm.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=q)])
                raw = (res.content or "").strip().upper()
                if raw in ("API", "RAG", "BOTH"):
                    decision = raw
            except Exception:
                raw = ""
        ql = q.lower()
        numeric_cues = (
            "how much should i invest", "per month", "monthly", "emi", "rate", "returns",
            "inflation", "years", "lakh", "crore", "down payment", "monthly contribution", "target amount",
            "sip per month", "monthly sip", "sip amount", "start a sip", "sip calculator"
        )
        edu_cues_strict = ("explain", "difference", "define", "how does", "how to", "why", "meaning", "mean", "what does", "concept", "guide")
        has_num = any(w in ql for w in numeric_cues)
        has_edu_core = any(w in ql for w in edu_cues_strict)
        # 'what is' counts as edu only when numeric not present
        what_is_present = "what is" in ql
        has_edu = has_edu_core or (what_is_present and not has_num)
        if decision is None:
            if has_num and has_edu:
                decision = "BOTH"
            elif has_num:
                decision = "API"
            elif has_edu:
                decision = "RAG"
            else:
                decision = "RAG"
        print(f"--- SUB-ROUTER: Model='{raw}' -> Selected [{decision}] ---")
        # Return route and preserve user_input to ensure downstream nodes receive it
        return {"route": decision, "user_input": s.get("user_input", "")}

    def choose(s: dict[str, Any]) -> str:
        return s.get("route", "RAG")

    goal_planning_graph = StateGraph(dict)
    goal_planning_graph.add_node("router", goal_planning_router_node)
    goal_planning_graph.add_node("api", goal_planning_api_node)
    goal_planning_graph.add_node("rag", goal_planning_rag_node)
    goal_planning_graph.add_node("synthesis", goal_planning_synthesis_node)
    goal_planning_graph.add_edge(START, "router")
    goal_planning_graph.add_conditional_edges("router", choose, {"API": "api", "RAG": "rag", "BOTH": "synthesis"})
    goal_planning_graph.add_edge("api", END)
    goal_planning_graph.add_edge("rag", END)
    goal_planning_graph.add_edge("synthesis", END)

    goal_planning_app = goal_planning_graph.compile()
    goal_planning_output = goal_planning_app.invoke({"user_input": state.get("user_input", "")})
    return {"response": goal_planning_output.get("response", "")}
