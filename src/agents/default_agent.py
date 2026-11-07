from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from workflow.aiFinanceWorkflow import FinanceWorkflowState


def default_node(state: dict[str, Any]) -> dict[str, Any]:
    return {"response": f"[Default Agent]: Out of Syllabus for -> '{state['user_input']}'"}