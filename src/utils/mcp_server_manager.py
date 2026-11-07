import asyncio
import subprocess
import sys
import threading
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = PROJECT_ROOT / "src" / "mcp" / "server" / "aiFinanceAssistant_server.py"
SERVER_URL = "http://127.0.0.1:8080/mcp"
REQUIRED_TOOLS = {
    "finance_qa_tool",
    "goal_planning_tool",
    "market_alpha_vantage_tool",
    "alpha_vantage_news_tool",
    "portfolio_alpha_vantage_tool",
    "tax_education_tool",
    "mediawiki_summary_tool",
}

_startup_lock = threading.Lock()
_server_process: subprocess.Popen[bytes] | None = None
_active_workflows = 0


async def _server_is_ready() -> bool:
    try:
        async with streamable_http_client(SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=3)
                result = await asyncio.wait_for(session.list_tools(), timeout=3)
                available_tools = {tool.name for tool in result.tools}
                return REQUIRED_TOOLS.issubset(available_tools)
    except Exception:
        return False


def _is_server_ready() -> bool:
    return asyncio.run(_server_is_ready())


def ensure_mcp_server_running(timeout: float = 20) -> None:
    """Start the local streamable-HTTP MCP server if it is not already ready."""
    global _server_process

    with _startup_lock:
        _ensure_server_locked(timeout)


def _ensure_server_locked(timeout: float) -> None:
    global _server_process

    if _server_process is not None and _server_process.poll() is not None:
        _server_process = None
    if _is_server_ready():
        print(f"MCP server is up and running at {SERVER_URL}", flush=True)
        return

    _server_process = subprocess.Popen(
        [
            sys.executable,
            str(SERVER_PATH),
            "--transport",
            "streamable-http",
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ],
        cwd=str(PROJECT_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _server_process.poll() is not None:
            _server_process = None
            raise RuntimeError(
                "The AI Finance MCP server exited before becoming ready on "
                "http://127.0.0.1:8080/mcp. Check the server startup output."
            )
        if _is_server_ready():
            print(f"MCP server is up and running at {SERVER_URL}", flush=True)
            return
        time.sleep(0.25)

    _stop_server_locked()
    raise RuntimeError(
        "The AI Finance MCP server did not become ready at "
        "http://127.0.0.1:8080/mcp. The port may already be in use."
    )


def begin_workflow() -> None:
    """Ensure the server is available and record an active workflow execution."""
    global _active_workflows

    with _startup_lock:
        _ensure_server_locked(timeout=20)
        _active_workflows += 1


def end_workflow() -> None:
    """Release a workflow execution and stop the server when none remain."""
    global _active_workflows

    with _startup_lock:
        if _active_workflows == 0:
            return
        _active_workflows -= 1
        if _active_workflows == 0:
            _stop_server_locked()


def _stop_server_locked() -> None:
    global _server_process

    process = _server_process
    _server_process = None
    if process is None or process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    print("MCP server has been stopped.", flush=True)
