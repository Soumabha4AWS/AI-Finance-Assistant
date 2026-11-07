from __future__ import annotations
from typing import Any
import os
import json
import requests

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class AlphaArgs(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g., AAPL")
    function: str = Field("GLOBAL_QUOTE", description="Alpha Vantage function (default GLOBAL_QUOTE)")


class FinanceQAAlphaTool(BaseTool):
    name: str = "alpha_vantage_tool"
    description: str = (
        "Calls Alpha Vantage using environment key (ALPHAVANTAGE_API_KEY) and returns a compact string for "
        "GLOBAL_QUOTE (latest price + change), or trimmed JSON for other functions/errors."
    )
    args_schema: type[BaseModel] = AlphaArgs

    def _run(self, symbol: str, function: str = "GLOBAL_QUOTE") -> str:  # type: ignore[override]
        key = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not key:
            return "Missing ALPHAVANTAGE_API_KEY"
        try:
            url = "https://www.alphavantage.co/query"
            params = {"function": function, "symbol": symbol, "apikey": key}
            r = requests.get(url, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
            # Common API messages
            if isinstance(data, dict) and data.get("Note"):
                return f"Rate limited: {data['Note']}"
            if isinstance(data, dict) and data.get("Error Message"):
                return f"API error: {data['Error Message']}"
            if function.upper() == "GLOBAL_QUOTE":
                quote = data.get("Global Quote") or {}
                price = quote.get("05. price") or quote.get("05. Price")
                change = quote.get("09. change") or quote.get("09. Change")
                pct = quote.get("10. change percent") or quote.get("10. Change Percent")
                if price:
                    return f"{symbol} price={price} change={change or 'N/A'} ({pct or 'N/A'})"
            # Fallback: trimmed JSON
            return json.dumps(data)[:800]
        except Exception as e:
            return f"Exception: {e}"

    async def _arun(self, symbol: str, function: str = "GLOBAL_QUOTE") -> str:  # type: ignore[override]
        return self._run(symbol=symbol, function=function)
