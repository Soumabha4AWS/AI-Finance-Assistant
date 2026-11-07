# Agent Modules

This folder contains the nodes used by the top-level finance workflow. Each
node receives a state dictionary, reads `user_input`, and generally returns a
dictionary containing `response`. The main graph is assembled in
[`../workflow/aiFinanceWorkflow.py`](../workflow/aiFinanceWorkflow.py).

## Agent overview

| Module | Node | Responsibility |
|---|---|---|
| [`router_agent.py`](./router_agent.py) | `router_node` | Classifies the user question and selects a specialist agent. It uses the model configured by `OPENAI_MODEL` and keyword routing as a fallback. |
| [`finance_qa_agent.py`](./finance_qa_agent.py) | `finance_qa_node` | Answers finance questions. Its inner router selects API, RAG, or BOTH; BOTH combines API data and retrieved context. |
| [`market_analysis_agent.py`](./market_analysis_agent.py) | `market_analysis_node` | Handles market-data and market-concept questions using API, RAG, or combined output. |
| [`portfolio_analysis_agent.py`](./portfolio_analysis_agent.py) | `portfolio_analysis_node` | Handles portfolio questions, routing between portfolio data, retrieved guidance, or both. |
| [`goal_planning_agent.py`](./goal_planning_agent.py) | `goal_planning_node` | Handles savings and investment-goal questions, selecting calculation/tooling, RAG guidance, or both. |
| [`news_synthesizer_agent.py`](./news_synthesizer_agent.py) | `news_synthesizer_node` | Handles current financial news and news-related education using API, RAG, or combined output. |
| [`tax_education_agent.py`](./tax_education_agent.py) | `tax_education_node` | Handles tax education. Its router selects tax-tool/API information, RAG, or a combined response. |
| [`default_agent.py`](./default_agent.py) | `default_node` | Returns an out-of-scope response when the top-level router cannot place a request in a specialist category. |

## Request flow

1. The workflow sends the input state to `router_node`.
2. The router selects one of these route names:
   - `finance qa`
   - `market analysis`
   - `portfolio analysis`
   - `goal planning`
   - `news synthesizer`
   - `tax education`
   - `default`
3. A specialist agent builds and runs an inner LangGraph. Its router selects
   `API`, `RAG`, or `BOTH`. If the LLM router cannot make a valid selection,
   the specialist uses keyword-based rules; the default inner route is RAG.
4. For `BOTH`, the agent runs its API/tool and RAG branches and asks an LLM to
   combine the returned content. The synthesis prompt restricts it from adding
   unsupported facts.
5. The selected node returns the response to the top-level workflow.

## API/tool and retrieval modules

Agent nodes delegate source-specific work to modules outside this folder:

- API/tool handlers are in [`../api/`](../api/).
- Retrieval and FAISS operations are in [`../rag/`](../rag/).
- Tool implementations are in [`../tools/`](../tools/).
- MCP server and client code are in [`../mcp/`](../mcp/). Finance Q&A, market
  analysis, and portfolio API handlers currently call their corresponding
  tools through the MCP client.

The workflow router, specialist routers, and synthesis nodes use the model
configured by `OPENAI_MODEL` (defaults to `gpt-4o-mini`). RAG branches may
require `OPENAI_API_KEY` and the embedding model configured by
`OPENAI_EMBEDDINGS_MODEL`; external API branches may require service-specific
credentials.
