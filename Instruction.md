# AI Finance Assistant - Execution Guide

## Requirements

- Windows with PowerShell
- Python 3.12
- API keys for the features you plan to use:
  - `OPENAI_API_KEY` for LLM and embedding-backed workflow features.
  - `OPENAI_MODEL` for the chat model used throughout the agents and API handlers. Defaults to `gpt-4o-mini`.
  - `ALPHAVANTAGE_API_KEY` for market, finance, news, and portfolio data. The alternate name `ALPHA_VANTAGE_API_KEY` is also supported.

Create a `.env` file in the project root and add the keys you have:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
ALPHAVANTAGE_API_KEY=your-alpha-vantage-api-key
OPENAI_EMBEDDINGS_MODEL=your-openai-embedding-model
```

Keep `.env` private; do not commit API keys.

## Install dependencies

Run these commands from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents environment activation, use the venv Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Launch the Gradio UI

From the project root:

```powershell
.\.venv\Scripts\python.exe .\src\web_app\ui_aiFinanceWorkflow.py
```

Open the local URL printed by Gradio in your browser. Enter a finance question and select **Run workflow**. The workflow checks the MCP service on `127.0.0.1:8080` before processing a request; if needed, it starts the service and stops the process it started when workflow execution completes.

## Run a workflow test

The test script runs a list of example finance queries. From the project root:

```powershell
.\.venv\Scripts\python.exe .\src\workflow\run_workflow\test_aiFinanceWorkflow.py
```

The examples may call external LLM and finance data APIs. Configure the corresponding keys in `.env` first.

## Run the MCP server manually

To serve MCP over Streamable HTTP on port 8080, run this in a terminal:

```powershell
.\.venv\Scripts\python.exe .\src\mcp\server\aiFinanceAssistant_server.py --transport streamable-http --host 127.0.0.1 --port 8080
```

The MCP endpoint is:

```text
http://127.0.0.1:8080/mcp
```

Keep the terminal open while the server is in use. Press **Ctrl+C** to stop it. A server started manually is external to the workflow and is not stopped by workflow cleanup.

## Run the MCP client example

The client example launches the MCP server using stdio, lists its tools, and calls the goal-planning tool:

```powershell
.\.venv\Scripts\python.exe .\src\mcp\client\aiFinanceAssistant_client.py
```

This is separate from the Streamable HTTP server mode above; the client starts and manages its own stdio server process.
