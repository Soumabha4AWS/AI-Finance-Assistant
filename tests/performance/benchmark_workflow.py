import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agents import router_agent


QUERIES = [
    "What is the difference between a mutual fund and an ETF?",
    "How much should I save monthly to retire in 25 years?",
    "Analyze my portfolio allocation for diversification.",
    "What is the stock trend for AAPL today?",
    "Summarize today's financial news and its market impact.",
    "What are the tax advantages of a Roth IRA?",
    "Explain compound interest with a simple example.",
    "Tell me about goal-based investing and risk appetite.",
]


def benchmark_router(rounds: int = 50) -> dict[str, float]:
    router_agent.llm = None
    durations: list[float] = []

    for _ in range(rounds):
        start = time.perf_counter()
        for query in QUERIES:
            router_agent.router_node({"user_input": query})
        durations.append(time.perf_counter() - start)

    return {
        "min_seconds": min(durations),
        "max_seconds": max(durations),
        "avg_seconds": statistics.mean(durations),
        "median_seconds": statistics.median(durations),
    }


def main() -> None:
    stats = benchmark_router()
    print("Router benchmark (heuristic routing):")
    for key, value in stats.items():
        print(f"{key}: {value:.6f}s")


if __name__ == "__main__":
    main()
