from __future__ import annotations

import json
import os
from typing import Any, Optional


def _default_index_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "indexes", "news_synthesizer")


def _news_synthesizer_json_path() -> str:
    return os.path.join(os.path.dirname(__file__), "documents", "news_synthesizer_qa.json")


def build_news_synthesizer_faiss(index_dir: Optional[str] = None) -> str:
    """Build and save a FAISS index from news_synthesizer_qa.json."""
    from dotenv import load_dotenv

    load_dotenv()
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
    except ImportError as exc:
        raise RuntimeError(f"Missing LangChain FAISS/OpenAI embeddings packages: {exc}") from exc

    json_path = _news_synthesizer_json_path()
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"news_synthesizer_qa.json not found at: {json_path}")

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("news_synthesizer_qa.json must contain a list of Q&A entries")

    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        question = str(row.get("question", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if not question or not answer:
            continue
        texts.append(question)
        metadatas.append(
            {
                "id": row.get("id"),
                "category": str(row.get("category", "")).strip(),
                "question": question,
                "answer": answer,
            }
        )

    if not texts:
        raise ValueError("No valid Q&A entries found in news_synthesizer_qa.json")

    index_path = index_dir or _default_index_dir()
    os.makedirs(index_path, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDINGS_MODEL"))
    vector_store = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
    vector_store.save_local(index_path)
    return index_path


def retrieve_news_synthesizer(
    query: str, index_dir: Optional[str] = None, k: int = 3
) -> list[dict[str, Any]]:
    """Retrieve the top-k news-synthesizer Q&A entries from a previously built index."""
    from dotenv import load_dotenv

    load_dotenv()
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
    except ImportError as exc:
        raise RuntimeError(f"Missing LangChain FAISS/OpenAI embeddings packages: {exc}") from exc

    query = query.strip()
    if not query:
        raise ValueError("A non-empty query is required")
    if k < 1:
        raise ValueError("k must be at least 1")

    index_path = index_dir or _default_index_dir()
    if not (
        os.path.isfile(os.path.join(index_path, "index.faiss"))
        and os.path.isfile(os.path.join(index_path, "index.pkl"))
    ):
        raise FileNotFoundError(
            f"News-synthesizer FAISS index not found at {index_path}; "
            "build it with build_news_synthesizer_faiss() first"
        )

    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDINGS_MODEL"))
    vector_store = FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )
    documents_scores = vector_store.similarity_search_with_score(query, k=k)

    results: list[dict[str, Any]] = []
    for document, score in documents_scores:
        metadata = document.metadata or {}
        results.append(
            {
                "id": metadata.get("id"),
                "category": metadata.get("category", ""),
                "question": metadata.get("question", ""),
                "answer": metadata.get("answer", ""),
                "score": float(score),
            }
        )
    return results


def news_synthesizer_rag_node(state: dict[str, Any]) -> dict[str, Any]:
    """Retrieve a news-synthesizer answer for the user's query."""
    user_input = (state.get("user_input") or "").strip()
    if not user_input:
        return {"response": "[RAG] No user query provided."}

    index_dir = _default_index_dir()
    try:
        if not (
            os.path.isfile(os.path.join(index_dir, "index.faiss"))
            and os.path.isfile(os.path.join(index_dir, "index.pkl"))
        ):
            build_news_synthesizer_faiss(index_dir)
        hits = retrieve_news_synthesizer(user_input, index_dir=index_dir, k=3)
    except Exception as exc:
        return {"response": f"[RAG] Error: {exc}"}

    if not hits:
        return {"response": "[RAG] No relevant entries found."}

    best = hits[0]
    return {"response": f"[RAG]\nQ: {best['question']}\nA: {best['answer']}"}
