"""
Text similarity for Layer 1, upgraded from raw word-overlap (TF-IDF) to
semantic similarity using sentence embeddings.

WHY THIS MATTERS: TF-IDF only measures shared words. A fraudster defeats it
trivially by rewording a copy-pasted report ("Fan #3 checked, operational"
-> "Ventilation fan number three inspected, functioning normally") -- same
lazy non-inspection, but TF-IDF similarity drops because the words changed.
Sentence embeddings compare MEANING, not exact wording, so a paraphrased
re-file is still caught.

HONESTY REQUIREMENT: this runs on the backend server, not the field device,
so it is not constrained by offline-first mobile requirements. But the
embedding model requires a one-time download from the internet on first
use. If that's unavailable (no internet at that moment, or a blocked
network), this module falls back to TF-IDF automatically rather than
crashing -- and every result honestly reports WHICH method actually ran,
so a fallback is never silently presented as the real thing.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Literal

SimilarityMethod = Literal["semantic_embedding", "tfidf_fallback"]

_model = None
_model_load_attempted = False


def _try_load_embedding_model():
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        # Any failure (no internet, model not cached, package missing, etc.)
        # -> fall back. We deliberately do not raise here: a live demo must
        # not crash because of a network hiccup.
        _model = None
    return _model


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        return 1.0 if text_a.strip() == text_b.strip() else 0.0
    return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])


def _semantic_similarity(text_a: str, text_b: str, model) -> float:
    from sklearn.metrics.pairwise import cosine_similarity
    embeddings = model.encode([text_a, text_b])
    return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])


def compute_similarity(text_a: str, text_b: str) -> tuple[float, SimilarityMethod]:
    """Returns (similarity_score, method_used). method_used is always
    reported honestly -- callers must surface it, not hide it."""
    if not text_a.strip() or not text_b.strip():
        return 0.0, "tfidf_fallback"

    model = _try_load_embedding_model()
    if model is not None:
        return _semantic_similarity(text_a, text_b, model), "semantic_embedding"

    return _tfidf_similarity(text_a, text_b), "tfidf_fallback"
