# Utilities

The `src/utils` package contains shared helpers for workflow configuration,
finance-query parsing, and managing the local AI Finance Assistant MCP server.

## Shared reusable helpers

`helper_reusable_items.py` provides:

- `get_openai_model()` loads the project `.env` file and returns the
  `OPENAI_MODEL` setting. It falls back to `gpt-4o-mini` if the setting is
  missing or blank.
- `get_alpha_vantage_key()` returns the Alpha Vantage key from
  `ALPHAVANTAGE_API_KEY` or `ALPHA_VANTAGE_API_KEY`, or `None` if neither is
  set.
- `extract_ticker(query)` heuristically finds one ticker, preferring a
  parenthesized symbol such as `(AAPL)`, then an uppercase token. It excludes
  common finance and general abbreviations to reduce false matches.
- `extract_symbols(query)` finds multiple symbols from parenthesized values,
  explicit `Symbol(s):` or `Ticker(s):` hints, and uppercase tokens. It
  uppercases and deduplicates results while preserving their order.
- `extract_weights_string(query)` extracts symbol-to-number weight pairs and
  returns them in a compact form such as `AAPL:60,MSFT:40`; it returns `None`
  when it finds no pairs.
- `extract_language_hint(query)` extracts a two-letter language code from a
  `Lang:` or `Language:` hint, returning `None` when absent.

These extractors use text heuristics, not a financial-data validator, so their
results should be treated as candidate values.

## MCP server lifecycle

`mcp_server_manager.py` manages the local MCP server over Streamable HTTP at
`http://127.0.0.1:8080/mcp`.

- `ensure_mcp_server_running(timeout=20)` checks that the server responds and
  exposes the required tools. If it is not ready, it starts the server using
  the current Python interpreter and waits for readiness up to the timeout.
- `begin_workflow()` ensures the server is available and increments the
  active-workflow count.
- `end_workflow()` decrements that count and stops the server when the last
  workflow finishes.

The startup lock prevents concurrent workflows from starting or stopping the
server at the same time. If the server exits before becoming ready or does
not start before the timeout, startup raises a `RuntimeError`. The manager
terminates its child server process when no workflows remain, escalating to a
kill if graceful shutdown does not complete promptly.