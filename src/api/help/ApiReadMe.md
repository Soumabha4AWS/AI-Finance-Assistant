# API and Tool-Call Nodes

This folder contains documentation for the workflow's API nodes in
[`../`](../). The Python modules themselves are in `src/api/`.

These modules are **not FastAPI or other HTTP route definitions**. Each exports
a function that an agent calls as a workflow node. The common interface is a
state dictionary containing `user_input` (and, where applicable, parsed
symbols), with a result shaped like `{"response": "..."}`. The agents decide
whether to invoke an API/tool node, a RAG node, or both.

## Modules that use the MCP client

| Module | Entry point | Purpose and implementation |
|---|---|---|
| [`finance_qa_api_mcp_client_call_agent.py`](../finance_qa_api_mcp_client_call_agent.py) | `finance_qa_api_node` | Retrieves a ticker's quote using the MCP client method `finance_qa_tool`, with Alpha Vantage `GLOBAL_QUOTE` as the requested function. It uses `state["ticker"]` when supplied or attempts to extract a ticker from `user_input`. Returns a message if the Alpha Vantage key or ticker is missing. Called by [`finance_qa_agent.py`](../../agents/finance_qa_agent.py). |
| [`market_analysis_api_mcp_client_call_agent.py`](../market_analysis_api_mcp_client_call_agent.py) | `market_analysis_api_node` | Retrieves market quote data through the MCP client method `market_alpha_vantage_tool`, requesting `GLOBAL_QUOTE`. Uses an existing ticker in state or extracts one from the user's text. Called by [`market_analysis_agent.py`](../../agents/market_analysis_agent.py). |
| [`portfolio_analysis_api_mcp_client_call_agent.py`](../portfolio_analysis_api_mcp_client_call_agent.py) | `portfolio_analysis_api_node` | Parses ticker symbols and optional weights from the user's text, then calls the MCP client method `portfolio_alpha_vantage_tool` for `GLOBAL_QUOTE` data. The tool summarizes per-symbol quotes and can estimate weighted daily change when weights and quote data are available. Called by [`portfolio_analysis_agent.py`](../../agents/portfolio_analysis_agent.py). |

These modules create an `AIFinanceAssistantClient` and call a registered MCP
tool method. The MCP client implementation is in
[`aiFinanceAssistant_client.py`](../../mcp/client/aiFinanceAssistant_client.py).

## Modules that call tools directly

| Module | Entry point | Tool and purpose |
|---|---|---|
| [`goal_planning_api_tool_call_agent.py`](../goal_planning_api_tool_call_agent.py) | `goal_planning_api_node` | Calls the local `GoalPlanningTool` directly (no MCP client and no external financial-data API). It computes a required monthly contribution from the target amount, years, and assumed annual return (10% by default). If the target or horizon cannot be determined, it asks for the missing information. Called by [`goal_planning_agent.py`](../../agents/goal_planning_agent.py). |
| [`news_synthesizer_api_tool_call_agent.py`](../news_synthesizer_api_tool_call_agent.py) | `news_synthesizer_api_node` | Uses the local `NewsAlphaTool`, which calls Alpha Vantage's `NEWS_SENTIMENT` endpoint. It derives ticker symbols from state or the user's text and returns a compact list of headlines. When the LangChain ReAct agent is available, it directs the model (configured by `OPENAI_MODEL`) to call the tool once; otherwise, it calls the tool directly. Called by [`news_synthesizer_agent.py`](../../agents/news_synthesizer_agent.py). |
| [`tax_education_api_tool_call_agent.py`](../tax_education_api_tool_call_agent.py) | `tax_education_api_node` | Uses the local `MediaWikiTool` to retrieve a tax-topic summary from Wikipedia. It infers a language hint and recognizes a few common tax topics, then uses a ReAct agent when available or calls the tool directly as a fallback. The model is selected by `OPENAI_MODEL`. This module does not currently call the tax MCP client method. Called by [`tax_education_agent.py`](../../agents/tax_education_agent.py). |

## External services and local tools

- **Alpha Vantage** provides finance quotes, market quotes, portfolio quote
  inputs, and news. Set `ALPHAVANTAGE_API_KEY` (or the supported alternate
  `ALPHA_VANTAGE_API_KEY`) in the project environment. Finance, market, and
  portfolio quote requests go through MCP; news requests use a local tool.
- **Wikipedia / MediaWiki** provides the tax-education node's topic summaries.
  The current node uses `MediaWikiTool` directly and does not require an
  Alpha Vantage key.
- **Goal planning** is calculated locally by `GoalPlanningTool`; it does not
  need a third-party market-data API.
- **OpenAI chat model** is used by the news and tax ReAct nodes (and by the
  separate agent routers/synthesis nodes). Configure `OPENAI_API_KEY` and
  optionally `OPENAI_MODEL`; the default model is `gpt-4o-mini`.

The MCP server separately registers a `tax_education_tool`; the tax API node
currently uses `MediaWikiTool` directly instead. See
[`aiFinanceAssistant_server.py`](../../mcp/server/aiFinanceAssistant_server.py)
and [`aiFinanceAssistant_client.py`](../../mcp/client/aiFinanceAssistant_client.py)
for the registered MCP tools and client methods.

## Error and output behavior

The nodes return tool/API text in the `response` field so their parent agent can
pass it through or combine it with RAG content. Missing credentials or
unrecognized symbols are reported in that response. Underlying tool failures,
such as service errors or rate limits, are returned by the tool implementation
as response text; they are not workflow HTTP status codes.