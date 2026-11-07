import argparse
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

load_dotenv(PROJECT_ROOT / ".env")

from tools.finance_qa_tools import FinanceQAAlphaTool
from tools.goal_planning_tools import GoalPlanningTool
from tools.market_analysis_tools import MarketAlphaTool
from tools.news_synthesizer_tools import NewsAlphaTool
from tools.portfolio_analysis_tools import PortfolioAlphaTool
from tools.tax_education_tools import MediaWikiTool, TaxEducationTool


server = MCPServer(name="aiFinanceAssistant")

finance_qa = FinanceQAAlphaTool()
goal_planning = GoalPlanningTool()
market_analysis = MarketAlphaTool()
news_synthesizer = NewsAlphaTool()
portfolio_analysis = PortfolioAlphaTool()
tax_education = TaxEducationTool()
mediawiki_summary = MediaWikiTool()


@server.tool(name="finance_qa_tool", description=finance_qa.description)
def finance_qa_tool(symbol: str, function: str = "GLOBAL_QUOTE") -> str:
    """Fetch an Alpha Vantage quote or other symbol data."""
    return finance_qa.invoke({"symbol": symbol, "function": function})


@server.tool(name=goal_planning.name, description=goal_planning.description)
def goal_planning_tool(
    user_input: Optional[str] = None,
    target: Optional[float] = None,
    years: Optional[int] = None,
    annual_rate: Optional[float] = None,
) -> str:
    """Calculate the monthly investment needed to reach a savings goal."""
    return goal_planning.invoke(
        {
            "user_input": user_input,
            "target": target,
            "years": years,
            "annual_rate": annual_rate,
        }
    )


@server.tool(name=market_analysis.name, description=market_analysis.description)
def market_alpha_vantage_tool(
    symbol: str, function: str = "GLOBAL_QUOTE"
) -> str:
    """Fetch an Alpha Vantage market quote or other symbol data."""
    return market_analysis.invoke({"symbol": symbol, "function": function})


@server.tool(name=news_synthesizer.name, description=news_synthesizer.description)
def alpha_vantage_news_tool(
    tickers: Optional[str] = None,
    topics: Optional[str] = None,
    function: str = "NEWS_SENTIMENT",
) -> str:
    """Fetch recent financial news from Alpha Vantage."""
    return news_synthesizer.invoke(
        {"tickers": tickers, "topics": topics, "function": function}
    )


@server.tool(name=portfolio_analysis.name, description=portfolio_analysis.description)
def portfolio_alpha_vantage_tool(
    symbols: str,
    function: str = "GLOBAL_QUOTE",
    weights: Optional[str] = None,
) -> str:
    """Fetch quotes and summarize a portfolio of ticker symbols."""
    return portfolio_analysis.invoke(
        {"symbols": symbols, "function": function, "weights": weights}
    )


@server.tool(name=tax_education.name, description=tax_education.description)
def tax_education_tool(topic: str, jurisdiction: Optional[str] = "US") -> str:
    """Explain a supported tax topic for the selected jurisdiction."""
    return tax_education.invoke({"topic": topic, "jurisdiction": jurisdiction})


@server.tool(name=mediawiki_summary.name, description=mediawiki_summary.description)
def mediawiki_summary_tool(
    topic: str, language: str = "en", intro_only: bool = True
) -> str:
    """Fetch an educational Wikipedia summary for a topic."""
    return mediawiki_summary.invoke(
        {"topic": topic, "language": language, "intro_only": intro_only}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Finance Assistant MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.transport == "streamable-http":
        server.run(transport=args.transport, host=args.host, port=args.port)
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()