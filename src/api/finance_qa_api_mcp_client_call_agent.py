from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _extract_ticker(query: str) -> str | None:
    if not query:
        return None
    match = re.search(r"\(([A-Za-z0-9.\-]{1,6})\)", query)
    if match:
        return match.group(1).upper()
    candidates = re.findall(r"\b[A-Z]{1,6}\b", query)
    stop_words = {
        "ETF",
        "USD",
        "NAV",
        "PE",
        "P",
        "EPS",
        "AI",
        "IPO",
        "CEO",
        "USA",
        "FII",
        "GDP",
    }
    return next(
        (
            candidate
            for candidate in candidates
            if candidate not in stop_words and len(candidate) >= 2
        ),
        None,
    )


def finance_qa_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """Fetch finance Q&A market data through the AI Finance MCP client."""
    load_dotenv()

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get(
        "ALPHA_VANTAGE_API_KEY"
    )
    if not api_key:
        return {"response": "Missing ALPHAVANTAGE_API_KEY in environment/.env"}

    user_input = (state.get("user_input") or "").strip()
    symbol = state.get("ticker") or _extract_ticker(user_input) or ""
    if not symbol:
        return {"response": "Could not detect a ticker symbol from your message"}

    mcp_src_path = Path(__file__).resolve().parents[1] / "mcp"
    if str(mcp_src_path) not in sys.path:
        sys.path.insert(0, str(mcp_src_path))
    from client.aiFinanceAssistant_client import AIFinanceAssistantClient

    async def call_finance_tool() -> str:
        async with AIFinanceAssistantClient() as client:
            return await client.finance_qa_tool(
                symbol=symbol,
                function="GLOBAL_QUOTE",
            )

    response = asyncio.run(call_finance_tool())
    return {"response": response}
