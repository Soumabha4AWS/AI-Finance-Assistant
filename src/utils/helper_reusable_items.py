from __future__ import annotations
from typing import Optional
import os
import re

# Shared helpers used across API/agent nodes and tools.


def get_openai_model() -> str:
    """Return the configured OpenAI chat model, preserving the existing default."""
    from dotenv import load_dotenv

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(project_root, ".env"))
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"


def get_alpha_vantage_key() -> Optional[str]:
    """Return Alpha Vantage API key from common env var names, or None if missing."""
    return os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")


def _dedup_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in items:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def extract_ticker(query: str) -> Optional[str]:
    """Extract a likely single ticker from text.

    Heuristics:
    - Parenthesized token like (AAPL)
    - All-caps 1–6 letters, excluding common stopwords
    Returns uppercased ticker or None.
    """
    if not query:
        return None
    m = re.search(r"\(([A-Za-z0-9.\-]{1,6})\)", query)
    if m:
        return m.group(1).upper()
    caps = re.findall(r"\b[A-Z]{1,6}\b", query)
    stop = {"ETF", "USD", "NAV", "PE", "P", "EPS", "AI", "IPO", "CEO", "USA", "FII", "GDP"}
    for c in caps:
        if c not in stop and len(c) >= 2:
            return c
    return None


def extract_symbols(query: str) -> list[str]:
    """Extract multiple tickers from free text.

    Sources:
    - Parentheses, e.g. (AAPL)
    - Explicit hints: Symbols:/Tickers:
    - All-caps tokens, excluding stopwords
    Returns uppercased unique list preserving order.
    """
    if not query:
        return []
    syms: list[str] = []
    syms += [m.upper() for m in re.findall(r"\(([A-Za-z0-9.\-]{1,6})\)", query)]
    m = re.search(r"(?:symbols?|tickers?)\s*:\s*([A-Za-z0-9.,\-\s]+)", query, flags=re.I)
    if m:
        parts = re.split(r"[\s,]+", m.group(1))
        syms += [p.strip().upper() for p in parts if p.strip()]
    caps = re.findall(r"\b[A-Z]{1,6}\b", query)
    stop = {"ETF", "USD", "NAV", "PE", "P", "EPS", "AI", "IPO", "CEO", "USA", "FII", "GDP"}
    for c in caps:
        if c not in stop and len(c) >= 2:
            syms.append(c)
    return _dedup_preserve_order(syms)


def extract_weights_string(query: str) -> Optional[str]:
    """Extract weights as a compact string like "AAPL:60,MSFT:40" if present; else None.

    Matches both inline pairs and a trailing "Weights:" hint line.
    """
    if not query:
        return None
    pairs = re.findall(r"([A-Za-z]{1,6})\s*:\s*(\d+(?:\.\d+)?)%?", query)
    if not pairs:
        m = re.search(r"weights?\s*:\s*([^\n]+)", query, flags=re.I)
        if m:
            pairs = re.findall(r"([A-Za-z]{1,6})\s*:\s*(\d+(?:\.\d+)?)%?", m.group(1))
    if not pairs:
        return None
    return ",".join([f"{sym.upper()}:{val}" for sym, val in pairs])


def extract_language_hint(query: str) -> Optional[str]:
    """Extract a 2-letter language code from "Lang:" or "Language:" hints; default handling is caller's."""
    if not query:
        return None
    m = re.search(r"(?:lang|language)\s*:\s*([a-z]{2})\b", query, flags=re.I)
    if m:
        return m.group(1).lower()
    return None
