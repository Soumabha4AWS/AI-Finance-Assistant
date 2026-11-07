import os
import sys
from typing import Any, TypedDict
from IPython.display import display, Image
from langgraph.graph import StateGraph, START, END

# Ensure 'src' is on sys.path when running this file directly (python src/workflow/aiFinanceWorkflow.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.router_agent import router_node, route_decision
from agents.finance_qa_agent import finance_qa_node
from agents.portfolio_analysis_agent import portfolio_analysis_node
from agents.market_analysis_agent import market_analysis_node
from agents.goal_planning_agent import goal_planning_node
from agents.news_synthesizer_agent import news_synthesizer_node
from agents.tax_education_agent import tax_education_node
from agents.default_agent import default_node
from utils.mcp_server_manager import begin_workflow, end_workflow


# 1. Define the state structure to hold the user input
class FinanceWorkflowState(TypedDict):
    user_input: str
    selected_agent: str
    response: str

# 2. Initialize the StateGraph
financeWorkflow = StateGraph(FinanceWorkflowState)

# 3. Add the node to the graph
financeWorkflow.add_node("router", router_node)
financeWorkflow.add_node("default", default_node)
financeWorkflow.add_node("finance_qa", finance_qa_node)
financeWorkflow.add_node("portfolio_analysis", portfolio_analysis_node)
financeWorkflow.add_node("market_analysis", market_analysis_node)
financeWorkflow.add_node("goal_planning", goal_planning_node)
financeWorkflow.add_node("news_synthesizer", news_synthesizer_node)
financeWorkflow.add_node("tax_education", tax_education_node)

# 4. Define edges
financeWorkflow.add_edge(START, "router")

# Add Conditional Edges from Router to Respective Agents
financeWorkflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "finance qa": "finance_qa",
        "portfolio analysis": "portfolio_analysis",
        "market analysis": "market_analysis",
        "goal planning": "goal_planning",
        "news synthesizer": "news_synthesizer",
        "tax education": "tax_education",
        "default": "default",
    },
)

# Connect all specialized agents to the END node
financeWorkflow.add_edge("finance_qa", END)
financeWorkflow.add_edge("portfolio_analysis", END)
financeWorkflow.add_edge("market_analysis", END)
financeWorkflow.add_edge("goal_planning", END)
financeWorkflow.add_edge("news_synthesizer", END)
financeWorkflow.add_edge("tax_education", END)
financeWorkflow.add_edge("default", END)

# 5. Compile the workflow app
compiled_finance_app = financeWorkflow.compile()


class ManagedFinanceApp:
    """Run each workflow with a matching MCP server lifecycle."""

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        begin_workflow()
        try:
            return compiled_finance_app.invoke(*args, **kwargs)
        finally:
            end_workflow()

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        import asyncio

        await asyncio.to_thread(begin_workflow)
        try:
            return await compiled_finance_app.ainvoke(*args, **kwargs)
        finally:
            await asyncio.to_thread(end_workflow)

    def __getattr__(self, name: str) -> Any:
        return getattr(compiled_finance_app, name)


financeApp = ManagedFinanceApp()

# print("\n" + "-"*80)

# 6. View the graph
# print(f"✓ Viewing the graph")  
# print(financeApp.get_graph().draw_ascii())
# print(f"✓ Viewed the graph")

# print("\n" + "-"*80)