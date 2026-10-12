from __future__ import annotations

"""Unified LLM access layer for the Day-24 RAG pipeline (m5 enrichment + RAGAS).

The generation/judge stages use the OpenAI Responses API (Muse Spark), but the
RAG pipeline and RAGAS need a chat/completions model. Both share the same
OpenAI-compatible endpoint and key.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (EMBEDDING_MODEL, ENRICH_MODEL, LLM_ENABLED, OPENAI_API_KEY,
                    OPENAI_BASE_URL, OPENAI_SESSION_ID, RAGAS_LLM_MODEL)

_HEADERS = {"x-opencode-session": OPENAI_SESSION_ID, "User-Agent": "lab24-rag/1.0"}


def llm_enabled() -> bool:
    return LLM_ENABLED


def get_client():
    """Return an OpenAI-compatible chat client for the configured endpoint."""
    from openai import OpenAI

    kwargs: dict = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    kwargs["default_headers"] = _HEADERS
    return OpenAI(**kwargs)


def chat(messages: list[dict], max_tokens: int = 400, temperature: float = 0.0,
         model: str | None = None) -> str:
    """Chat completion, returns text (empty on failure)."""
    client = get_client()
    resp = client.chat.completions.create(
        model=model or ENRICH_MODEL, messages=messages,
        max_tokens=max_tokens, temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def get_ragas_llm():
    """LangChain LLM wrapped for RAGAS (chat/completions model)."""
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    kwargs: dict = {"model": RAGAS_LLM_MODEL, "api_key": OPENAI_API_KEY, "temperature": 0.0}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    kwargs["default_headers"] = _HEADERS
    return LangchainLLMWrapper(ChatOpenAI(**kwargs))


def get_ragas_embeddings():
    """Local bge-m3 embeddings wrapped for RAGAS (no embeddings endpoint needed)."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    return LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    ))
