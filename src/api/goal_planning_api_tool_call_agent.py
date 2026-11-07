from __future__ import annotations
from typing import Any


def goal_planning_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """Goal Planning API node: compute required monthly investment deterministically.

    This node calls GoalPlanningTool directly with the user's message to avoid
    LLM/agent variability. It reads 'user_input' from state and returns
    {"response": <concise sentence>}.
    """
    # Local imports to keep function self-contained
    from dotenv import load_dotenv
    from tools.goal_planning_tools import GoalPlanningTool

    load_dotenv()

    user_input = (state.get("user_input") or "").strip()

    goalPlanningTool = GoalPlanningTool()
    output = goalPlanningTool._run(user_input=user_input)
    return {"response": output}
