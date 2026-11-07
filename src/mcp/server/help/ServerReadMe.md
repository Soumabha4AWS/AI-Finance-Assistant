# AI Finance Assistant MCP Server

The server implementation is
[`aiFinanceAssistant_server.py`](../aiFinanceAssistant_server.py). It exposes
the project's finance, market, portfolio, news, goal-planning, and tax
information tools through the Model Context Protocol (MCP), so an MCP client
can discover and invoke them using a common interface.

## What the server does

At startup, the module:

1. Selects the installed MCP server implementation (`MCPServer`, with a
   `FastMCP` compatibility fallback).
2. Adds the project's `src` directory to Python's import path and loads the
   project-root `.env` file.
3. Creates the local tool instances and registers their callable functions
   with the MCP server named `aiFinanceAssistant`.
4. Starts the server using the selected transport.

Each registered function delegates to its corresponding tool's `invoke()`
method and returns the tool's response string. The server is the MCP interface;
the underlying finance calculations and external-service requests live in the
tool implementations in `src/tools/`.

## Registered tools

| MCP tool | Purpose | Main inputs |
|---|---|---|
| `finance_qa_tool` | Retrieves Alpha Vantage data for one finance ticker. | `symbol`; optional `function` (defaults to `GLOBAL_QUOTE`). |
| `goal_planning_tool` | Calculates the monthly investment needed for a savings goal. | Optional `user_input`, `target`, `years`, and `annual_rate`. |
| `market_alpha_vantage_tool` | Retrieves Alpha Vantage market data for one symbol. | `symbol`; optional `function` (defaults to `GLOBAL_QUOTE`). |
| `alpha_vantage_news_tool` | Retrieves recent news/sentiment from Alpha Vantage. | Optional `tickers`, `topics`, and `function` (defaults to `NEWS_SENTIMENT`). |
| `portfolio_alpha_vantage_tool` | Retrieves quotes for multiple symbols and summarizes them, optionally calculating a weighted daily change. | `symbols`; optional `function` (defaults to `GLOBAL_QUOTE`) and `weights`. |
| `tax_education_tool` | Provides an explanation for a supported tax topic and jurisdiction. | `topic`; optional `jurisdiction` (defaults to `US`). |
| `mediawiki_summary_tool` | Retrieves an educational Wikipedia summary. | `topic`; optional `language` (defaults to `en`) and `intro_only` (defaults to `true`). |

Tool names and descriptions are made available to MCP clients for discovery.
`goal_planning_tool`, `tax_education_tool`, and `mediawiki_summary_tool` use
local tool implementations; the quote and news tools use Alpha Vantage.

## Transports and launch options

The command-line entry point supports two transports:

- **stdio** (default): intended for a client that launches and communicates
  with the server process over standard input/output.
- **Streamable HTTP**: provides an HTTP MCP endpoint. The default host is
  `127.0.0.1`, the default port is `8080`, and the MCP path is `/mcp`.

From the project root in PowerShell, start the HTTP server with:

```powershell
python .\src\mcp\server\aiFinanceAssistant_server.py --transport streamable-http --host 127.0.0.1 --port 8080
```

For stdio mode, run:

```powershell
python .\src\mcp\server\aiFinanceAssistant_server.py
```

The HTTP server can also be started automatically by the workflow's
[`mcp_server_manager.py`](../../../utils/mcp_server_manager.py), which checks
that the server is ready and that the expected tools are registered.

## Configuration and prerequisites

- Install the project dependencies, including the MCP SDK and the
  integrations used by the tools.
- Set `ALPHAVANTAGE_API_KEY` in the project-root `.env` for Alpha Vantage
  quote and news features. The tool implementations also accept
  `ALPHA_VANTAGE_API_KEY`.
- OpenAI configuration is needed only for tools that use OpenAI internally;
  tool configuration is otherwise handled by the corresponding tool module.

The server binds to loopback by default for local use. An alternate host can
be supplied with `--host`; choose network exposure deliberately and configure
appropriate access controls outside this server if it is made reachable by
other machines.

## Related files

- [`../aiFinanceAssistant_server.py`](../aiFinanceAssistant_server.py) —
  server setup, MCP registrations, and command-line transport selection.
- [`../../client/aiFinanceAssistant_client.py`](../../client/aiFinanceAssistant_client.py) —
  project MCP client and tool-call wrappers.
- [`../../../utils/mcp_server_manager.py`](../../../utils/mcp_server_manager.py) —
  workflow-managed HTTP server startup, readiness checks, and shutdown.
- [`../../../tools/`](../../../tools/) — underlying tool implementations.