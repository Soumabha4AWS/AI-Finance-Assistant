from __future__ import annotations
from typing import Any, Optional


def _default_index_dir() -> str:
    import os
    here = os.path.dirname(__file__)
    idx_dir = os.path.join(here, "indexes", "finance_qa")
    os.makedirs(idx_dir, exist_ok=True)
    return idx_dir


def _finance_qa_json_path() -> str:
    import os
    here = os.path.dirname(__file__)
    return os.path.join(here, "documents", "finance_qa.json")


def build_finance_qa_faiss(index_dir: Optional[str] = None) -> str:
    """Build a FAISS index from rag/documents/finance_qa.json and save it to index_dir.

    Returns the index directory path. Requires OPENAI_API_KEY for embeddings.
    """
    import os
    import json
    from dotenv import load_dotenv
    load_dotenv()
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
    except Exception as e:
        raise RuntimeError(f"Missing LangChain FAISS/OpenAI embeddings packages: {e}")

    idx_dir = index_dir or _default_index_dir()

    json_path = _finance_qa_json_path()
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"finance_qa.json not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []
    # Expected schema: list of {"question": str, "answer": str} (ignore extras)
    for row in data if isinstance(data, list) else []:
        q = str(row.get("question", "")).strip()
        a = str(row.get("answer", "")).strip()
        if not q or not a:
            continue
        txt = f"Q: {q}\nA: {a}"
        texts.append(txt)
        metadatas.append({"question": q, "answer": a})

    if not texts:
        raise ValueError("No Q&A pairs found in finance_qa.json")
    embeddingModel = os.getenv("OPENAI_EMBEDDINGS_MODEL")
    embeddings = OpenAIEmbeddings(model=embeddingModel)
    vs = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
    vs.save_local(idx_dir)
    return idx_dir


def retrieve_finance_qa(query: str, index_dir: Optional[str] = None, k: int = 3) -> list[dict[str, Any]]:
    """Retrieve top-k Q&A entries from the FAISS index for the given query.

    Returns a list of {question, answer, score} sorted by similarity (lower score = closer).
    If index is missing, it is built automatically from finance_qa.json.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
    except Exception as e:
        raise RuntimeError(f"Missing LangChain FAISS/OpenAI embeddings packages: {e}")

    idx_dir = index_dir or _default_index_dir()
    if not (os.path.isdir(idx_dir) and os.listdir(idx_dir)):
        build_finance_qa_faiss(idx_dir)
    embeddingModel = os.getenv("OPENAI_EMBEDDINGS_MODEL")
    embeddings = OpenAIEmbeddings(model=embeddingModel)
    # allow_dangerous_deserialization is required for FAISS legacy pickle store
    vs = FAISS.load_local(idx_dir, embeddings, allow_dangerous_deserialization=True)
    docs_scores = vs.similarity_search_with_score(query, k=k)

    results: list[dict[str, Any]] = []
    for doc, score in docs_scores:
        md = doc.metadata or {}
        results.append({
            "question": md.get("question", ""),
            "answer": md.get("answer", ""),
            "score": float(score),
        })
    return results


def finance_qa_rag_node(state: dict[str, Any]) -> dict[str, Any]:
    """Finance Q&A RAG node: retrieve answers from FAISS index built from finance_qa.json.

    - Generation: build_finance_qa_faiss(index_dir) — run once or when index is missing.
    - Retrieval: retrieve_finance_qa(query, index_dir, k) — returns top matches.
    """
    user_input = (state.get("user_input") or "").strip()
    if not user_input:
        return {"response": "[RAG] No user query provided."}

    try:
        hits = retrieve_finance_qa(user_input, index_dir=None, k=3)
    except Exception as e:
        return {"response": f"[RAG] Error: {e}"}

    if not hits:
        return {"response": "[RAG] No relevant entries found."}

    # Return the top answer with brief context; keep deterministic and non-fabricating
    best = hits[0]
    q = best.get("question", "")
    a = best.get("answer", "")
    return {"response": f"[RAG]\nQ: {q}\nA: {a}"}
