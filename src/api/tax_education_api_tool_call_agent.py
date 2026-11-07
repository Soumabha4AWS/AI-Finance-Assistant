from __future__ import annotations
from typing import Any


def tax_education_api_node(state: dict[str, Any]) -> dict[str, Any]:
    """ReAct agent (single-tool) for Tax Education using Wikipedia (no API key).

    Returns {response: <tool-output>}.
    Extracts a topic and optional language from user_input and calls MediaWikiTool.
    """
    # Local imports to keep function self-contained
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from tools.tax_education_tools import MediaWikiTool
    from utils.helper_reusable_items import extract_language_hint, get_openai_model
    try:
        from langchain.agents import create_react_agent, AgentExecutor  # type: ignore
        HAS_REACT = True
    except Exception:
        HAS_REACT = False

    load_dotenv()

    def _guess_topic(query: str) -> str | None:
        ql = (query or "").lower()
        heuristics = [
            (["wash sale"], "Wash sale"),
            (["capital gains"], "Capital gains tax"),
            (["qualified dividend"], "Qualified dividend"),
        ]
        for keys, title in heuristics:
            if all(k in ql for k in keys):
                return title
        return None

    user_input = (state.get("user_input") or "").strip()
    language = extract_language_hint(user_input) or "en"
    topic_hint = _guess_topic(user_input)

    llm = ChatOpenAI(model=get_openai_model(), temperature=0.0)
    wikiTool = MediaWikiTool()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a tax education agent. You MUST call the provided tool exactly once to answer. "
         "After the tool returns, output ONLY the tool's returned content verbatim. Do NOT fabricate. "
         "Infer 'topic' from the user's message; infer optional 'language' (2-letter) from 'Lang:' or 'Language:' hints. "
         "If a 'Topic:' hint is present, use it verbatim as the tool's topic."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    # Build input for the agent with explicit hints to bias extraction
    input_text = user_input or ""
    if topic_hint:
        input_text = f"{input_text}\n\nTopic: {topic_hint}" if input_text else f"Topic: {topic_hint}"
    if language:
        input_text = f"{input_text}\nLanguage: {language}"

    if HAS_REACT:
        agent = create_react_agent(llm=llm, tools=[wikiTool], prompt=prompt)  # type: ignore[name-defined]
        executor = AgentExecutor(agent=agent, tools=[wikiTool], verbose=False, handle_parsing_errors=True)  # type: ignore[name-defined]
        result = executor.invoke({"input": input_text})
        output = result.get("output", "")
        return {"response": output}
    else:
        # Fallback: call tool directly; prefer heuristic topic when available
        topic = topic_hint or user_input or "tax"
        output = wikiTool._run(topic=topic, language=language, intro_only=True)
        return {"response": output}
