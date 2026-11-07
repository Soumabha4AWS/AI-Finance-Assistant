from __future__ import annotations
from typing import Optional
import re

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class GoalPlanArgs(BaseModel):
    user_input: Optional[str] = Field(None, description="Original user message for inline parsing")
    target: Optional[float] = Field(None, description="Target corpus amount (same currency as user)")
    years: Optional[int] = Field(None, description="Horizon in years")
    annual_rate: Optional[float] = Field(None, description="Expected annual return in percent, e.g. 10 for 10%")


def _parse_amount(text: str) -> Optional[float]:
    if not text:
        return None
    t = text.lower().replace(",", "")
    m = re.search(r"(?:₹|rs\.?|inr|\$)?\s*([0-9]+(?:\.[0-9]+)?)\s*(lakh|lac|k|m|million|crore|cr)?", t)
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(2) or "").lower()
    mult = 1.0
    if unit == "k":
        mult = 1e3
    elif unit in {"m", "million"}:
        mult = 1e6
    elif unit in {"lakh", "lac"}:
        mult = 1e5
    elif unit in {"crore", "cr"}:
        mult = 1e7
    return val * mult


def _parse_years(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d{1,3})\s*(years?|yrs?)", text.lower())
    if m:
        return int(m.group(1))
    m2 = re.search(r"\b(\d{1,2})\b", text)
    if m2:
        return int(m2.group(1))
    return None


def _pmt_for_target(target: float, years: int, annual_rate: float) -> float:
    r = annual_rate / 100.0 / 12.0
    n = years * 12
    if r <= 0:
        return target / max(n, 1)
    return target * r / ((1 + r) ** n - 1)


class GoalPlanningTool(BaseTool):
    name: str = "goal_planning_tool"
    description: str = (
        "Computes required monthly investment for a goal using user_input or explicit args: "
        "target, years, annual_rate%. Assumes end-of-month contributions; returns a concise "
        "sentence with computed monthly amount and assumptions."
    )
    args_schema: type[BaseModel] = GoalPlanArgs

    def _run(
        self,
        user_input: Optional[str] = None,
        target: Optional[float] = None,
        years: Optional[int] = None,
        annual_rate: Optional[float] = None,
    ) -> str:  # type: ignore[override]
        ui = user_input or ""
        tgt = target if target is not None else _parse_amount(ui)
        yrs = years if years is not None else _parse_years(ui)
        rate = annual_rate if annual_rate is not None else 10.0
        if tgt is None or yrs is None:
            return "Insufficient data: please provide a target amount and horizon (years)."
        pmt = _pmt_for_target(tgt, yrs, rate)
        return f"Monthly investment required ≈ {pmt:,.2f} (target={tgt:,.0f}, years={yrs}, annual_return={rate:.1f}%)."

    async def _arun(  # type: ignore[override]
        self,
        user_input: Optional[str] = None,
        target: Optional[float] = None,
        years: Optional[int] = None,
        annual_rate: Optional[float] = None,
    ) -> str:
        return self._run(user_input=user_input, target=target, years=years, annual_rate=annual_rate)
