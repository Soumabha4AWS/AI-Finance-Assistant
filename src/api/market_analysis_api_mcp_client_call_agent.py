from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from utils.helper_reusable_items import extract_ticker, get_alpha_vantage_key


def market_analysis_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """Fetch market data through the AI Finance MCP client."""
    load_dotenv()

    if not get_alpha_vantage_key():
        return {"response": "Missing ALPHAVANTAGE_API_KEY in environment/.env"}

    user_input = (state.get("user_input") or "").strip()
    symbol = state.get("ticker") or extract_ticker(user_input) or ""
    if not symbol:
        return {"response": "Could not detect a ticker symbol from your message"}

    mcp_src_path = Path(__file__).resolve().parents[1] / "mcp"
    if str(mcp_src_path) not in sys.path:
        sys.path.insert(0, str(mcp_src_path))
    from client.aiFinanceAssistant_client import AIFinanceAssistantClient

    async def call_market_tool() -> str:
        async with AIFinanceAssistantClient() as client:
            return await client.market_alpha_vantage_tool(
                symbol=symbol,
                function="GLOBAL_QUOTE",
            )

    response = asyncio.run(call_market_tool())
    return {"response": response}
