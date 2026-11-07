from __future__ import annotations
from typing import Any, Optional
import os
import json
import requests

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class NewsAlphaArgs(BaseModel):
    tickers: Optional[str] = Field(None, description="Comma-separated tickers, e.g., AAPL,MSFT")
    topics: Optional[str] = Field(None, description="Optional topics keywords")
    function: str = Field("NEWS_SENTIMENT", description="Alpha Vantage news function")


class NewsAlphaTool(BaseTool):
    name: str = "alpha_vantage_news_tool"
    description: str = (
        "Fetches recent news via Alpha Vantage NEWS_SENTIMENT using env key ALPHAVANTAGE_API_KEY. "
        "Returns a compact string of the top headlines (titles, optional source/time)."
    )
    args_schema: type[BaseModel] = NewsAlphaArgs

    def _run(self, tickers: Optional[str] = None, topics: Optional[str] = None, function: str = "NEWS_SENTIMENT") -> str:  # type: ignore[override]
        key = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not key:
            return "Missing ALPHAVANTAGE_API_KEY"
        try:
            url = "https://www.alphavantage.co/query"
            params = {"function": function, "apikey": key}
            if tickers:
                params["tickers"] = tickers
            if topics:
                params["topics"] = topics
            r = requests.get(url, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and data.get("Note"):
                return f"Rate limited: {data['Note']}"
            if isinstance(data, dict) and data.get("Error Message"):
                return f"API error: {data['Error Message']}"
            feed = data.get("feed") if isinstance(data, dict) else None
            if not feed:
                return json.dumps(data)[:800]
            # Build a compact list of top 3 headlines
            items = []
            for item in feed[:3]:
                title = item.get("title") or "(no title)"
                source = item.get("source") or ""
                time_published = item.get("time_published") or ""
                if source and time_published:
                    items.append(f"- {title} — {source} ({time_published})")
                elif source:
                    items.append(f"- {title} — {source}")
                else:
                    items.append(f"- {title}")
            return "\n".join(items)
        except Exception as e:
            return f"Exception: {e}"

    async def _arun(self, tickers: Optional[str] = None, topics: Optional[str] = None, function: str = "NEWS_SENTIMENT") -> str:  # type: ignore[override]
        return self._run(tickers=tickers, topics=topics, function=function)
