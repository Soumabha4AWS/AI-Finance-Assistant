from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Any
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import re
from utils.helper_reusable_items import get_openai_model

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState

# Load variables from the .env file into the system environment
load_dotenv()
# 0. Initialize the LLM using the configured OpenAI chat model.
try:
    llm = ChatOpenAI(model=get_openai_model(), temperature=0.0)
except Exception:
    llm = None  # Fallback to heuristic router when LLM is unavailable (e.g., missing API key)

# 1. Define Conditional Routing Edge Function

def route_decision(state: dict[str, Any]) -> Literal[
    "finance qa",
    "portfolio analysis",
    "market analysis",
    "goal planning",
    "news synthesizer",
    "tax education",
    "default",
]:
    return state["selected_agent"]

# 2. Define the Workflow Router Node

def router_node(state: dict[str, Any]) -> dict[str, Any]:
    """Analyzes the user query and routes it to one of the 6 specialized agents."""
    query = state["user_input"]
    
    system_prompt = (
        "You are an expert financial workflow router. "
        "Classify the user's query into EXACTLY one of the following category KEYS and reply with the exact key ONLY (no quotes, code blocks, punctuation, or explanation):\n"
        "- finance_qa\n"
        "- portfolio_analysis\n"
        "- market_analysis\n"
        "- goal_planning\n"
        "- news_synthesizer\n"
        "- tax_education\n"
        "If uncertain, respond with: default"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]

    raw = ""
    if llm is not None:
        try:
            result = llm.invoke(messages)
            raw = (result.content or "").strip().lower()
        except Exception:
            raw = ""

    norm = raw.replace(" ", "_")
    norm = re.sub(r"[^a-z_]+", "", norm)
    compressed = norm.replace("_", "")
    norm_spaces = norm.replace("_", " ")

    valid_routes = {
        "finance qa",
        "portfolio analysis",
        "market analysis",
        "goal planning",
        "news synthesizer",
        "tax education",
        "default",
    }

    if norm_spaces in valid_routes:
        selected_agent = norm_spaces
    else:
        selected_agent = next((vr for vr in valid_routes if vr.replace(" ", "") == compressed), None)
        if not selected_agent:
            ql = query.lower()
            if any(kw in ql for kw in ["portfolio", "allocation", "diversification", "rebalance", "holdings", "exposure"]):
                selected_agent = "portfolio analysis"
            elif any(kw in ql for kw in ["market", "stock", "price", "trend", "quote", "ticker", "today"]):
                selected_agent = "market analysis"
            elif any(kw in ql for kw in ["goal", "retire", "retirement", "college", "planning", "risk appetite", "horizon"]):
                selected_agent = "goal planning"
            elif any(kw in ql for kw in ["news", "headline", "article", "summar", "breaking", "update"]):
                selected_agent = "news synthesizer"
            elif any(kw in ql for kw in ["tax", "capital gains", "deduction", "income tax", "irs", "section"]):
                selected_agent = "tax education"
            elif any(kw in ql for kw in ["what is", "explain", "difference", "define", "how does", "meaning", "concept"]):
                selected_agent = "finance qa"
            else:
                selected_agent = "default"

    print(f"--- ROUTER: Model='{raw}' -> Selected [{selected_agent}] ---")
    return {"selected_agent": selected_agent}

    
    # Fallback to finance_qa if classification is unclear
    valid_routes = {
        "finance qa", 
        "portfolio analysis", 
        "market analysis", 
        "goal planning", 
        "news synthesizer", 
        "tax education"
    }
    
    selected_agent = route_key if route_key in valid_routes else "default"
    print(f"--- ROUTER: Directed query to [{selected_agent}] ---")
    
    return {"selected_agent": selected_agent}