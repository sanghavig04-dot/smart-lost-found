"""Scoring logic for pairing lost items with found items. Pure functions, no I/O."""
import re

import numpy as np

from . import config

STOPWORDS = {
    "the", "and", "with", "for", "was", "near", "left", "has", "have", "this",
    "that", "from", "found", "lost", "item", "my", "our", "a", "an", "in", "on",
    "at", "of", "to", "is", "it", "its", "black", "white",
}


def tokens(*parts: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", " ".join(p or "" for p in parts).lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def text_score(a: dict, b: dict) -> float:
    """0..1 from shared keywords (title, description, location) and category."""
    ta = tokens(a.get("title"), a.get("description"), a.get("location"))
    tb = tokens(b.get("title"), b.get("description"), b.get("location"))
    overlap = len(ta & tb) / min(len(ta), len(tb)) if ta and tb else 0.0
    same_category = 1.0 if a.get("category") and a.get("category") == b.get("category") else 0.0
    return 0.7 * overlap + 0.3 * same_category


def image_score(ea, eb) -> float | None:
    """0..1 from cosine similarity of two embeddings, or None if either is missing."""
    if not ea or not eb:
        return None
    a, b = np.asarray(ea, dtype="float32"), np.asarray(eb, dtype="float32")
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return None
    cos = float(a @ b) / denom
    floor = config.IMAGE_FLOOR
    return float(np.clip((cos - floor) / (1 - floor), 0.0, 1.0))


def score(a: dict, b: dict) -> float:
    txt = text_score(a, b)
    img = image_score(a.get("embedding"), b.get("embedding"))
    if img is None:
        return txt
    return config.IMAGE_WEIGHT * img + (1 - config.IMAGE_WEIGHT) * txt


def rank_matches(item: dict, candidates: list[dict], threshold: float | None = None, limit: int = 5):
    """Return [(score, candidate)] above the threshold, best first."""
    cutoff = config.MATCH_THRESHOLD if threshold is None else threshold
    scored = [(score(item, c), c) for c in candidates]
    scored = [(s, c) for s, c in scored if s >= cutoff]
    scored.sort(key=lambda sc: sc[0], reverse=True)
    return scored[:limit]
