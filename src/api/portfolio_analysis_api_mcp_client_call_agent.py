from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from utils.helper_reusable_items import (
    extract_symbols,
    extract_weights_string,
    get_alpha_vantage_key,
)


def portfolio_analysis_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """Fetch portfolio data through the AI Finance MCP client."""
    load_dotenv()

    api_key = get_alpha_vantage_key()
    user_input = (state.get("user_input") or "").strip()
    symbols = extract_symbols(user_input)
    weights = extract_weights_string(user_input)

    if not api_key:
        return {"response": "Missing ALPHAVANTAGE_API_KEY in environment/.env"}
    if not symbols:
        return {"response": "Could not detect any ticker symbols from your message"}

    mcp_src_path = Path(__file__).resolve().parents[1] / "mcp"
    if str(mcp_src_path) not in sys.path:
        sys.path.insert(0, str(mcp_src_path))
    from client.aiFinanceAssistant_client import AIFinanceAssistantClient

    async def call_portfolio_tool() -> str:
        async with AIFinanceAssistantClient() as client:
            return await client.portfolio_alpha_vantage_tool(
                symbols=",".join(symbols),
                function="GLOBAL_QUOTE",
                weights=weights,
            )

    response = asyncio.run(call_portfolio_tool())
    return {"response": response}
