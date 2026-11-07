# Finance Assistant Tools

The modules in `src/tools` define LangChain tools used by the AI Finance
Assistant. Each tool declares its name, input schema, and description so an
agent can select it and pass structured arguments. Tools provide synchronous
`_run()` and asynchronous `_arun()` entry points; the asynchronous methods
delegate to the same underlying operation.

## Available tools

### Finance Q&A — `finance_qa_tools.py`

`FinanceQAAlphaTool` (tool name: `alpha_vantage_tool`) requests data from the
Alpha Vantage API for a ticker symbol. By default, it requests `GLOBAL_QUOTE`
and formats the latest price, change, and percent change as a compact string.
For other API functions, it returns up to 800 characters of JSON.

Inputs: required `symbol`; optional `function` (default `GLOBAL_QUOTE`).

### Goal planning — `goal_planning_tools.py`

`GoalPlanningTool` (tool name: `goal_planning_tool`) estimates the monthly
investment needed to reach a target amount over a specified number of years.
It assumes contributions are made at the end of each month. If explicit
`target`, `years`, or `annual_rate` values are not provided, it tries to parse
the target and time horizon from `user_input`; the annual return defaults to
10%. Amounts may include units such as `k`, `million`, `lakh`, or `crore`.

Inputs: optional `user_input`, `target`, `years`, and `annual_rate` (percent).
The result includes the estimated monthly amount and calculation assumptions.
If the target or horizon cannot be determined, it asks for the missing
information.

### Market analysis — `market_analysis_tools.py`

`MarketAlphaTool` (tool name: `market_alpha_vantage_tool`) fetches Alpha
Vantage market data for a ticker or index. For the default `GLOBAL_QUOTE`
function, it returns price and daily change details; for other functions, it
returns a compact JSON response.

Inputs: required `symbol`; optional `function` (default `GLOBAL_QUOTE`).

### News — `news_synthesizer_tools.py`

`NewsAlphaTool` (tool name: `alpha_vantage_news_tool`) requests financial
news from Alpha Vantage, using its `NEWS_SENTIMENT` function by default. It
can filter by comma-separated tickers and/or topic keywords, and returns up to
three headlines with source and publication time when available.

Inputs: optional `tickers`, `topics`, and `function` (default
`NEWS_SENTIMENT`).

### Portfolio analysis — `portfolio_analysis_tools.py`

`PortfolioAlphaTool` (tool name: `portfolio_alpha_vantage_tool`) fetches data
for multiple ticker symbols and formats a per-symbol summary. With
`GLOBAL_QUOTE`, it reports each symbol's price and daily change. Optional
weights such as `AAPL:50,MSFT:50` are normalized and used to estimate the
weighted daily percent change when quote percentages are available.

Inputs: required comma-separated `symbols`; optional `function` (default
`GLOBAL_QUOTE`) and comma-separated `weights`.

### Tax education and Wikipedia summaries — `tax_education_tools.py`

This module provides two tools:

- `TaxEducationTool` (tool name: `tax_education_tool`) returns a concise,
  built-in educational explanation for supported topics such as capital
  gains, wash sales, cost basis, dividends, retirement accounts, and tax
  credits versus deductions. It accepts a `topic` and optional
  `jurisdiction` (default `US`). The jurisdiction is included as context in
  the response; the content is educational and is not tax or legal advice.
- `MediaWikiTool` (tool name: `mediawiki_summary_tool`) fetches a topic
  summary from Wikipedia's public API without an API key. It accepts a
  `topic`, language code (default `en`), and `intro_only` flag (default
  `True`). For a few recognized tax topics it tries a canonical page title
  first, then searches Wikipedia if needed. Returned text is capped at 1,200
  characters and includes a Wikipedia source label and educational disclaimer.

## API keys and error responses

The Alpha Vantage tools require an API key in the environment variable
`ALPHAVANTAGE_API_KEY` or `ALPHA_VANTAGE_API_KEY`. They return a message when
the key is missing, the service rate-limits a request, or the API reports an
error. HTTP and other request failures are returned as exception text.

Goal planning and tax education calculations/explanations are local and do not
require an external API key. The Wikipedia summary tool uses the public
Wikipedia API. Its lookup helpers fall back between summary and search
endpoints and return a no-summary message if no usable result is found.