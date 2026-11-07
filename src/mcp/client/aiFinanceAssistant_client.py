import sys
from pathlib import Path
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVER_PATH = PROJECT_ROOT / "src" / "mcp" / "server" / "aiFinanceAssistant_server.py"


class AIFinanceAssistantClient:
    """Async stdio client for the AI Finance Assistant MCP tools.

    Use as an async context manager to keep one server process alive while
    making multiple tool calls.
    """

    def __init__(self) -> None:
        self._stdio_context: Any = None
        self._session_context: Any = None
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "AIFinanceAssistantClient":
        server = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_PATH)],
            cwd=str(PROJECT_ROOT),
        )
        self._stdio_context = stdio_client(server)
        read_stream, write_stream = await self._stdio_context.__aenter__()
        self._session_context = ClientSession(read_stream, write_stream)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        if self._session_context is not None:
            await self._session_context.__aexit__(exc_type, exc_value, traceback)
        if self._stdio_context is not None:
            await self._stdio_context.__aexit__(exc_type, exc_value, traceback)
        self._session = None

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if self._session is None:
            raise RuntimeError(
                "Client is not connected. Use 'async with AIFinanceAssistantClient()'."
            )

        result = await self._session.call_tool(name, arguments)
        text = "\n".join(
            block.text
            for block in result.content
            if getattr(block, "type", None) == "text"
        )
        is_error = getattr(result, "is_error", getattr(result, "isError", False))
        if is_error:
            raise RuntimeError(f"MCP tool '{name}' failed: {text}")
        return text

    async def list_tools(self) -> list[str]:
        """Return the names of tools exposed by the connected server."""
        if self._session is None:
            raise RuntimeError(
                "Client is not connected. Use 'async with AIFinanceAssistantClient()'."
            )
        result = await self._session.list_tools()
        return [tool.name for tool in result.tools]

    async def finance_qa_tool(
        self, symbol: str, function: str = "GLOBAL_QUOTE"
    ) -> str:
        """Call finance_qa_tool to fetch finance Q&A data for a ticker symbol."""
        return await self._call_tool(
            "finance_qa_tool", {"symbol": symbol, "function": function}
        )

    async def goal_planning_tool(
        self,
        user_input: Optional[str] = None,
        target: Optional[float] = None,
        years: Optional[int] = None,
        annual_rate: Optional[float] = None,
    ) -> str:
        """Call goal_planning_tool to calculate a monthly savings investment."""
        return await self._call_tool(
            "goal_planning_tool",
            {
                "user_input": user_input,
                "target": target,
                "years": years,
                "annual_rate": annual_rate,
            },
        )

    async def market_alpha_vantage_tool(
        self, symbol: str, function: str = "GLOBAL_QUOTE"
    ) -> str:
        """Call market_alpha_vantage_tool for market data."""
        return await self._call_tool(
            "market_alpha_vantage_tool",
            {"symbol": symbol, "function": function},
        )

    async def alpha_vantage_news_tool(
        self,
        tickers: Optional[str] = None,
        topics: Optional[str] = None,
        function: str = "NEWS_SENTIMENT",
    ) -> str:
        """Call alpha_vantage_news_tool to fetch recent financial news."""
        return await self._call_tool(
            "alpha_vantage_news_tool",
            {"tickers": tickers, "topics": topics, "function": function},
        )

    async def portfolio_alpha_vantage_tool(
        self,
        symbols: str,
        function: str = "GLOBAL_QUOTE",
        weights: Optional[str] = None,
    ) -> str:
        """Call portfolio_alpha_vantage_tool for portfolio quotes and summary."""
        return await self._call_tool(
            "portfolio_alpha_vantage_tool",
            {"symbols": symbols, "function": function, "weights": weights},
        )

    async def tax_education_tool(
        self, topic: str, jurisdiction: Optional[str] = "US"
    ) -> str:
        """Call tax_education_tool for an educational tax-topic explanation."""
        return await self._call_tool(
            "tax_education_tool",
            {"topic": topic, "jurisdiction": jurisdiction},
        )

    async def mediawiki_summary_tool(
        self,
        topic: str,
        language: str = "en",
        intro_only: bool = True,
    ) -> str:
        """Call mediawiki_summary_tool for a Wikipedia topic summary."""
        return await self._call_tool(
            "mediawiki_summary_tool",
            {"topic": topic, "language": language, "intro_only": intro_only},
        )


async def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    async with AIFinanceAssistantClient() as client:
        print("Available tools:", ", ".join(await client.list_tools()))
        print(
            await client.goal_planning_tool(
                target=1_000_000, years=10, annual_rate=0
            )
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())