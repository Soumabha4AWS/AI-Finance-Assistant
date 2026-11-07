# AI Finance Assistant MCP Client

`aiFinanceAssistant_client.py` provides an asynchronous Python client for
calling the tools exposed by the AI Finance Assistant MCP server. It launches
the local server as a subprocess and communicates with it over standard
input/output (stdio).

## Connecting

Use the client as an async context manager. Entering the context starts the
server and initializes the MCP session; leaving it closes the session and
server process.

```python
import asyncio

from src.mcp.client.aiFinanceAssistant_client import AIFinanceAssistantClient


async def main():
    async with AIFinanceAssistantClient() as client:
        tools = await client.list_tools()
        print(tools)
        answer = await client.finance_qa_tool("IBM")
        print(answer)


asyncio.run(main())
```

Calling a client method before entering the context raises a `RuntimeError`.

## Client methods

- `list_tools()` returns the names of the tools available from the connected
  server.
- `finance_qa_tool(symbol, function="GLOBAL_QUOTE")` gets finance Q&A data for
  a ticker symbol.
- `goal_planning_tool(user_input=None, target=None, years=None,
  annual_rate=None)` calculates a monthly savings investment plan.
- `market_alpha_vantage_tool(symbol, function="GLOBAL_QUOTE")` requests market
  data.
- `alpha_vantage_news_tool(tickers=None, topics=None,
  function="NEWS_SENTIMENT")` requests financial news.
- `portfolio_alpha_vantage_tool(symbols, function="GLOBAL_QUOTE",
  weights=None)` requests quotes and a portfolio summary.
- `tax_education_tool(topic, jurisdiction="US")` requests an educational
  explanation of a tax topic.
- `mediawiki_summary_tool(topic, language="en", intro_only=True)` requests a
  Wikipedia summary.

Tool methods return the text content supplied by the server. If a tool reports
an error, the client raises a `RuntimeError` containing the tool name and
error text.

## Running the file directly

Running `aiFinanceAssistant_client.py` directly lists the server's available
tools and demonstrates a goal-planning request for a target of 1,000,000 over
10 years at a 0% annual rate.