from __future__ import annotations
from typing import Optional
import re

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class TaxEduArgs(BaseModel):
    topic: str = Field(..., description="Tax topic to explain, e.g., 'capital gains', 'wash sale', 'tax credit vs deduction'")
    jurisdiction: Optional[str] = Field("US", description="Jurisdiction/country for context (default US)")


_TOPICS: dict[str, str] = {
    "capital_gains": (
        "Capital gains are profits when you sell an asset for more than its cost basis. "
        "Short-term (held ≤ 1 year) are typically taxed like ordinary income; long-term (held > 1 year) "
        "use preferential rates. Losses can offset gains; net losses may be carried forward subject to limits."
    ),
    "short_vs_long_term": (
        "Short-term gains: assets held one year or less; generally taxed at ordinary-income rates. "
        "Long-term gains: assets held more than one year; generally taxed at preferential capital-gains rates. "
        "The holding period runs from the day after acquisition to the day of sale."
    ),
    "wash_sale": (
        "A wash sale occurs if you sell a security at a loss and buy a substantially identical security within 30 days before or after the sale. "
        "The disallowed loss is added to the basis of the new shares; the loss is deferred, not permanently lost."
    ),
    "basis_methods": (
        "Cost basis is what you paid for an investment, adjusted for certain events. Common lot-relief methods include FIFO, LIFO, and specific identification. "
        "Your chosen method affects which lots are treated as sold and the gain/loss recognized."
    ),
    "qualified_dividends": (
        "Qualified dividends meet specific holding-period and issuer requirements and are generally taxed at long-term capital-gains rates. "
        "Non-qualified (ordinary) dividends are typically taxed at ordinary-income rates."
    ),
    "capital_loss_carryover": (
        "If capital losses exceed gains, the excess may offset limited ordinary income each year, with remaining losses carried forward to future years until used, subject to jurisdictional rules."
    ),
    "tax_credit_vs_deduction": (
        "A tax deduction reduces taxable income; its value equals the deduction times your marginal rate. "
        "A tax credit directly reduces tax owed dollar-for-dollar. Credits are generally more valuable than equal-sized deductions."
    ),
    "standard_vs_itemized": (
        "Taxpayers can usually claim a standard deduction or itemize eligible expenses (e.g., certain medical, taxes, mortgage interest, charity). "
        "Choose the higher total; you generally cannot take both. Thresholds and rules vary by year and filing status."
    ),
    "ira_roth_vs_traditional": (
        "Traditional IRA: potential pre-tax contributions; growth tax-deferred; withdrawals taxed as ordinary income; required minimum distributions apply. "
        "Roth IRA: post-tax contributions; qualified withdrawals generally tax-free; no RMDs during the original owner’s lifetime."
    ),
    "hsa_vs_fsa": (
        "HSA: for high-deductible health plans; contributions may be pre-tax, growth tax-free, and qualified medical withdrawals tax-free (triple tax advantage); unused funds roll over. "
        "FSA: employer-established; pre-tax contributions for eligible expenses; typically use-it-or-lose-it with limited carryover."
    ),
}

_SYNONYMS: dict[str, str] = {
    "capital gains": "capital_gains",
    "cap gains": "capital_gains",
    "short term vs long term": "short_vs_long_term",
    "short vs long": "short_vs_long_term",
    "washsale": "wash_sale",
    "wash sale": "wash_sale",
    "basis": "basis_methods",
    "cost basis": "basis_methods",
    "qualified dividend": "qualified_dividends",
    "qualified dividends": "qualified_dividends",
    "loss carryover": "capital_loss_carryover",
    "capital loss carryover": "capital_loss_carryover",
    "credit vs deduction": "tax_credit_vs_deduction",
    "standard deduction vs itemized": "standard_vs_itemized",
    "standard vs itemized": "standard_vs_itemized",
    "roth vs traditional ira": "ira_roth_vs_traditional",
    "ira (roth vs traditional)": "ira_roth_vs_traditional",
    "hsa vs fsa": "hsa_vs_fsa",
}


def _normalize(topic: str) -> str:
    t = re.sub(r"\s+", " ", topic.strip().lower())
    return _SYNONYMS.get(t, t.replace(" ", "_"))


class TaxEducationTool(BaseTool):
    name: str = "tax_education_tool"
    description: str = (
        "Provides concise, jurisdiction-agnostic tax education summaries for common topics. "
        "Educational only; not legal or tax advice."
    )
    args_schema: type[BaseModel] = TaxEduArgs

    def _run(self, topic: str, jurisdiction: Optional[str] = "US") -> str:  # type: ignore[override]
        key = _normalize(topic)
        text = _TOPICS.get(key)
        if not text:
            supported = ", ".join(sorted(k.replace("_", " ") for k in _TOPICS.keys()))
            return (
                "Unknown topic. Supported topics include: " + supported + ". "
                "This is educational information, not advice."
            )
        jur = (jurisdiction or "").upper()
        prefix = f"[Jurisdiction: {jur}] " if jur else ""
        return prefix + text + " (Educational summary; not tax, legal, or investment advice.)"

    async def _arun(self, topic: str, jurisdiction: Optional[str] = "US") -> str:  # type: ignore[override]
        return self._run(topic=topic, jurisdiction=jurisdiction)


class WikiSummaryArgs(BaseModel):
    topic: str = Field(..., description="Wikipedia page title or search query, e.g., 'Capital gains tax'")
    language: str = Field("en", description="Wikipedia language code, e.g., en, de, fr (default en)")
    intro_only: bool = Field(True, description="Return only the lead/intro summary when available (default True)")


class MediaWikiTool(BaseTool):
    name: str = "mediawiki_summary_tool"
    description: str = (
        "Fetches an educational summary from Wikipedia's public REST API (no key). "
        "Given a topic, returns the page summary. Falls back to a site search to resolve the best page. "
        "Educational use only; not legal or tax advice; Wikipedia content is CC BY-SA."
    )
    args_schema: type[BaseModel] = WikiSummaryArgs

    _WIKI_TITLES = {
        "wash_sale": "Wash sale",
        "capital_gains": "Capital gains tax",
        "qualified_dividends": "Qualified dividend",
    }

    def _run(self, topic: str, language: str = "en", intro_only: bool = True) -> str:  # type: ignore[override]
        import requests
        from urllib.parse import quote

        UA = {"User-Agent": "AI-Finance-Assistant/1.0 (educational; no-contact)", "Accept": "application/json"}

        def fetch_summary_rest(title: str) -> tuple[str, str, str] | None:
            base = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/" + quote(title.replace(" ", "_"))
            try:
                r = requests.get(base, timeout=12, headers=UA)
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                data = r.json()
                if not isinstance(data, dict):
                    return None
                t = str(data.get("title") or title)
                desc = str(data.get("description") or "")
                extract = str(data.get("extract") or "")
                return (t, desc, extract)
            except Exception:
                return None

        def search_first(query: str) -> tuple[str, int] | None:
            try:
                url = f"https://{language}.wikipedia.org/w/api.php"
                params = {"action": "query", "list": "search", "srsearch": query, "format": "json"}
                r = requests.get(url, params=params, timeout=12, headers=UA)
                r.raise_for_status()
                j = r.json()
                arr = (((j or {}).get("query") or {}).get("search") or [])
                if arr:
                    top = arr[0]
                    return (str(top.get("title")), int(top.get("pageid")))
                return None
            except Exception:
                return None

        def fetch_extract_pageid(pageid: int) -> tuple[str, str] | None:
            try:
                url = f"https://{language}.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": 1 if intro_only else 0,
                    "explaintext": 1,
                    "pageids": pageid,
                    "format": "json",
                }
                r = requests.get(url, params=params, timeout=12, headers=UA)
                r.raise_for_status()
                j = r.json()
                pages = ((j or {}).get("query") or {}).get("pages") or {}
                if not isinstance(pages, dict):
                    return None
                for _, info in pages.items():
                    title = str(info.get("title") or "")
                    extract = str(info.get("extract") or "")
                    if extract:
                        return (title, extract)
                return None
            except Exception:
                return None

        # Prefer canonical Wikipedia titles for known tax topics
        key = _normalize(topic)
        canonical = self._WIKI_TITLES.get(key)

        hit = None
        if canonical:
            rest = fetch_summary_rest(canonical)
            if rest:
                hit = rest

        # Strategy: search first, fetch by pageid; then fall back to REST by raw topic
        if not hit:
            sr = search_first(topic)
            if sr:
                title, pid = sr
                ex = fetch_extract_pageid(pid)
                if ex:
                    t, extract = ex
                    hit = (t, "", extract)
        if not hit:
            rest = fetch_summary_rest(topic)
            if rest:
                hit = rest
        if not hit:
            return "No Wikipedia summary found for the requested topic."

        title, desc, extract = hit
        header = title if not desc else f"{title} — {desc}"
        body = (extract or "").strip()
        if not body:
            return f"{header}\n(No summary content available.)"
        if len(body) > 1200:
            body = body[:1200].rstrip() + "…"
        return f"Source: Wikipedia ({language})\n{header}\n\n{body}\n\n(Educational summary; not tax, legal, or investment advice.)"

    async def _arun(self, topic: str, language: str = "en", intro_only: bool = True) -> str:  # type: ignore[override]
        return self._run(topic=topic, language=language, intro_only=intro_only)
