from __future__ import annotations
from typing import Any


def news_synthesizer_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """ReAct agent (single-tool) for News Synthesizer using Alpha Vantage NEWS_SENTIMENT.

    Returns {response: <answer-came-from-reactAgent>} and reads ALPHAVANTAGE_API_KEY from .env.
    """
    # Local imports to keep function self-contained
    import os
    import re
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from tools.news_synthesizer_tools import NewsAlphaTool
    from utils.helper_reusable_items import get_openai_model
    try:
        from langchain.agents import create_react_agent, AgentExecutor  # type: ignore
        HAS_REACT = True
    except Exception:
        HAS_REACT = False

    load_dotenv()

    def _extract_ticker_list(query: str) -> list[str]:
        res: list[str] = []
        if not query:
            return res
        for m in re.findall(r"\(([A-Za-z0-9.\-]{1,6})\)", query):
            res.append(m.upper())
        # Add ALLCAPS tokens too (deduplicate)
        for token in re.findall(r"\b[A-Z]{1,6}\b", query):
            if token.upper() not in res:
                res.append(token.upper())
        return res

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHA_VANTAGE_API_KEY")
    user_input = (state.get("user_input") or "").strip()
    tickers = state.get("tickers")
    if not tickers:
        tl = _extract_ticker_list(user_input)
        tickers = ",".join(tl) if tl else ""

    if not api_key:
        return {"response": "Missing ALPHAVANTAGE_API_KEY in environment/.env"}

    llm = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    newsAlphaTool = NewsAlphaTool()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a news agent. You MUST call the provided tool exactly once to answer. "
         "After the tool returns, output ONLY the tool's returned content verbatim. Do NOT fabricate. "
         "Infer 'tickers' from the user's message; if a 'Tickers:' hint is present, use it."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    if HAS_REACT:
        agent = create_react_agent(llm=llm, tools=[newsAlphaTool], prompt=prompt)  # type: ignore[name-defined]
        executor = AgentExecutor(agent=agent, tools=[newsAlphaTool], verbose=False, handle_parsing_errors=True)  # type: ignore[name-defined]
        input_text = user_input or ""
        if tickers:
            input_text = f"{input_text}\n\nTickers: {tickers}" if input_text else f"Tickers: {tickers}"
        result = executor.invoke({"input": input_text})
        output = result.get("output", "")
        return {"response": output}
    else:
        # Fallback: call tool directly
        output = newsAlphaTool._run(tickers=tickers or None, topics=None, function="NEWS_SENTIMENT")
        return {"response": output}
