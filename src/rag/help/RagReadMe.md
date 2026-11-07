# Retrieval-Augmented Generation (RAG)

The modules in `src/rag` provide retrieval-based answers for common questions
about the AI Finance Assistant's finance Q&A, goal planning, market analysis,
financial news, portfolio analysis, and tax education topics.

Despite the name, these agents do not generate a new answer with a language
model. They search a curated question-and-answer dataset and return the answer
from the closest matching entry. This makes responses grounded in the local
dataset, but means they do not provide live market data or news.

## How it works

1. Each domain has a JSON file in `src/rag/documents/` containing Q&A entries.
   Entries need non-empty `question` and `answer` fields; some datasets also
   include `id` and `category`.
2. The domain's `build_*_faiss()` function embeds the entries using the
   configured OpenAI embeddings model and saves a FAISS vector index under
   `src/rag/indexes/<domain>/`.
3. A `retrieve_*()` function embeds a query and searches the index for the
   closest matches. It returns up to three entries by default, each with its
   question, answer, and similarity score (lower scores indicate closer
   matches).
4. The corresponding `*_rag_node(state)` reads `state["user_input"]`,
   retrieves matches, and returns a state update containing `response`. The
   node returns the best match as `[RAG]`, followed by its question and answer.

An empty query produces a message that no query was provided; an unsuccessful
retrieval produces an error response or a no-relevant-entries message.

## Domains and modules

| Module | Dataset | Default index |
|---|---|---|
| `finance_qa_rag_agent.py` | `finance_qa.json` | `indexes/finance_qa/` |
| `goal_planning_rag_agent.py` | `goal_planning_qa.json` | `indexes/goal_planning/` |
| `market_analysis_rag_agent.py` | `market_analysis_qa.json` | `indexes/market_analysis/` |
| `news_synthesizer_rag_agent.py` | `news_synthesizer_qa.json` | `indexes/news_synthesizer/` |
| `portfolio_analysis_rag_agent.py` | `portfolio_analysis_qa.json` | `indexes/portfolio_analysis/` |
| `tax_education_rag_agent.py` | `tax_education_qa.json` | `indexes/tax_education/` |

## Configuration and index creation

Install the project's LangChain, FAISS, OpenAI embeddings, and `python-dotenv`
dependencies. Configure `OPENAI_API_KEY` and, optionally,
`OPENAI_EMBEDDINGS_MODEL` in the environment or a `.env` file. The OpenAI
embeddings model is used both when building an index and when searching it.

The node functions build an index if it is missing, then retrieve the top
matches. You can also build one explicitly by calling the domain's
`build_<domain>_faiss()` function, or retrieve multiple matches using
`retrieve_<domain>(query, index_dir=None, k=3)`. Direct retrieval requires an
existing index for the market-analysis, news-synthesizer, portfolio-analysis,
and tax-education domains; finance Q&A and goal planning build a missing index
automatically.