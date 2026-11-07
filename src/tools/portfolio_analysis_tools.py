from __future__ import annotations
from typing import Any, Optional
import os
import json
import re
import requests

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class PortfolioAlphaArgs(BaseModel):
    symbols: str = Field(..., description="Comma-separated tickers, e.g., AAPL,MSFT,GOOGL")
    function: str = Field("GLOBAL_QUOTE", description="Alpha Vantage function applied per symbol (default GLOBAL_QUOTE)")
    weights: Optional[str] = Field(
        None,
        description="Optional comma-separated weights as percents: e.g., AAPL:50,MSFT:50. Used to estimate weighted daily change.",
    )


def _parse_weights(spec: Optional[str]) -> dict[str, float]:
    if not spec:
        return {}
    pairs = [p.strip() for p in spec.split(",") if p.strip()]
    w: dict[str, float] = {}
    total = 0.0
    for p in pairs:
        if ":" in p:
            sym, val = p.split(":", 1)
            sym = sym.strip().upper()
            try:
                num = float(val.strip())
                if num < 0:
                    continue
                w[sym] = num
                total += num
            except Exception:
                continue
    if total > 0:
        for k in list(w.keys()):
            w[k] = w[k] / total  # normalize to 1.0
    return w


class PortfolioAlphaTool(BaseTool):
    name: str = "portfolio_alpha_vantage_tool"
    description: str = (
        "Fetches per-symbol quotes from Alpha Vantage (env ALPHAVANTAGE_API_KEY) and summarizes a portfolio. "
        "Input symbols as comma-separated tickers. Optionally provide weights like 'AAPL:50,MSFT:50' to estimate a "
        "weighted daily change using each symbol's change percent when available."
    )
    args_schema: type[BaseModel] = PortfolioAlphaArgs

    def _run(self, symbols: str, function: str = "GLOBAL_QUOTE", weights: Optional[str] = None) -> str:  # type: ignore[override]
        key = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not key:
            return "Missing ALPHAVANTAGE_API_KEY"
        try:
            syms = [s.strip().upper() for s in re.split(r"[\s,]+", symbols) if s.strip()]
            if not syms:
                return "No symbols provided"
            wmap = _parse_weights(weights)
            url = "https://www.alphavantage.co/query"
            lines = []
            agg_change = 0.0
            agg_has = False
            for sym in syms:
                params = {"function": function, "symbol": sym, "apikey": key}
                r = requests.get(url, params=params, timeout=12)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and data.get("Note"):
                    return f"Rate limited: {data['Note']}"
                if isinstance(data, dict) and data.get("Error Message"):
                    lines.append(f"{sym}: API error: {data['Error Message']}")
                    continue
                if function.upper() == "GLOBAL_QUOTE":
                    quote = data.get("Global Quote") or {}
                    price = quote.get("05. price") or quote.get("05. Price")
                    change = quote.get("09. change") or quote.get("09. Change")
                    pct = quote.get("10. change percent") or quote.get("10. Change Percent")
                    lines.append(f"{sym} price={price or 'N/A'} change={change or 'N/A'} ({pct or 'N/A'})")
                    # Aggregate weighted percent if available
                    if pct and sym in wmap and wmap[sym] > 0:
                        try:
                            p = float(str(pct).replace('%','').strip()) / 100.0
                            agg_change += wmap[sym] * p
                            agg_has = True
                        except Exception:
                            pass
                else:
                    # Fallback to trimmed JSON per symbol
                    lines.append(f"{sym} -> {json.dumps(data)[:300]}")
            header = f"Portfolio ({len(syms)} symbols)"
            if agg_has:
                header += f" | Weighted daily change ≈ {agg_change*100:.2f}%"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Exception: {e}"

    async def _arun(self, symbols: str, function: str = "GLOBAL_QUOTE", weights: Optional[str] = None) -> str:  # type: ignore[override]
        return self._run(symbols=symbols, function=function, weights=weights)
