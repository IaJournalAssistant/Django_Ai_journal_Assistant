"""Lightweight NLP utilities for tag prediction.

This module provides a small, safe wrapper around spaCy for predicting a single
tag for a piece of text. It prefers spaCy when available (and will use
`en_core_web_sm`), but falls back to a simple keyword/overlap-based heuristic
when spaCy or vectors are not available.

API:
- predict_tag(text, tag_objs=None) -> str|None  (best tag name or None)
- predict_tags_for_texts(texts, tag_objs) -> List[str|None]

Notes on performance:
- The module caches the loaded spaCy model so it isn't reloaded per-call.
- When predicting for multiple texts, prefer calling predict_tags_for_texts
  so the implementation can use spaCy's nlp.pipe for batching.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)

_NLP = None

# Optional mapping from Tag name (string) to list of keyword strings. If you
# prefer to provide this mapping from elsewhere, you can update this dict at
# runtime (e.g. import and assign) or pass a custom mapping in a future
# extension of the API.
TAG_KEYWORDS = {
    "Sad": ["sad", "upset", "crying", "tearful", "heartbroken", "depressed", "lonely", "miserable", "gloomy", "sorrow", "grief", "melancholy", "pain", "tragic"],
    
    "Happy": ["happy", "joy", "excited", "fun", "cheerful", "delighted", "glad", "ecstatic", "bliss", "smile", "laugh", "content", "thrilled", "relieved"],
    
    "Angry": ["angry", "mad", "frustrated", "annoyed", "furious", "irritated", "upset", "rage", "resentment", "bitter", "offended", "disgusted"],
    
    "Gossip": ["gossip", "rumor", "story", "tea", "drama", "juicy", "scandal", "spill", "dish", "trending", "news", "chat", "buzz", "inside scoop"],
    
    "Work": ["work", "office", "project", "deadline", "meeting", "task", "job", "career", "promotion", "boss", "colleague", "team", "assignment", "report"],
    
    "Travel": ["travel", "trip", "vacation", "holiday", "journey", "explore", "adventure", "flight", "hotel", "beach", "mountain", "city", "roadtrip", "tour"],
    
    "Food": ["food", "meal", "recipe", "cooking", "dish", "restaurant", "eat", "snack", "dinner", "lunch", "breakfast", "tasty", "yummy", "delicious", "cafe"],
    
    "Health": ["health", "fitness", "workout", "exercise", "gym", "diet", "nutrition", "wellness", "meditation", "doctor", "illness", "sick", "recover", "mental health"],
    
    "Love": ["love", "relationship", "heart", "romance", "dating", "crush", "partner", "affection", "valentine", "hug", "kiss", "marriage", "couple", "feelings"],
    
    "Hobby": ["hobby", "art", "music", "reading", "painting", "drawing", "writing", "photography", "gaming", "craft", "gardening", "diy", "dance", "singing"],
    
    "School": ["school", "class", "teacher", "homework", "exam", "study", "lecture", "assignment", "student", "college", "university", "course", "grade", "project"],
    
    "Tech": ["tech", "technology", "computer", "software", "hardware", "AI", "app", "programming", "coding", "gadget", "device", "startup", "innovation", "internet"],
    
    "Entertainment": ["movie", "series", "tv", "music", "concert", "show", "theater", "film", "episode", "celebrity", "star", "actor", "actress", "festival"],
    
    "Finance": ["money", "finance", "budget", "investment", "bank", "loan", "pay", "salary", "saving", "spending", "tax", "profit", "expense", "economy"],
    
    "Event": ["party", "celebration", "wedding", "birthday", "festival", "concert", "gathering", "ceremony", "anniversary", "event", "meeting", "ceremony"],
    
    "News": ["news", "update", "breaking", "announcement", "alert", "report", "headline", "trending", "journal", "media", "press", "story", "current", "information"]
}



def _load_nlp():
    """Lazily load a spaCy model (en_core_web_sm) if available.

    Returns the loaded nlp or None if spaCy isn't installed.
    """
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        import spacy  # type: ignore
    except Exception as e:  # pragma: no cover - environment dependent
        logger.debug("spaCy not available: %s", e)
        _NLP = None
        return None

    # Try to load a small English model. If it's not installed, fall back to a
    # blank English pipeline (similarity will be less accurate without vectors).
    try:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except Exception:
            # If the small model isn't installed, try to load whatever English
            # model is present or create a blank pipeline.
            try:
                _NLP = spacy.load("en")
            except Exception:
                _NLP = spacy.blank("en")
    except Exception as e:  # pragma: no cover - environment dependent
        logger.warning("Failed to initialize spaCy model: %s", e)
        _NLP = None

    return _NLP


def _token_overlap_score(a: str, b: str) -> float:
    a_tok = set([t for t in (a or "").lower().split() if t])
    b_tok = set([t for t in (b or "").lower().split() if t])
    if not a_tok or not b_tok:
        return 0.0
    return len(a_tok & b_tok) / float(len(a_tok | b_tok))


def predict_tags_for_texts(texts: Iterable[str], tag_objs: Iterable, top_k: int = 1) -> List[Optional[str]]:
    """Predict best tag name for each text in `texts`.

    Args:
        texts: iterable of text strings (note content)
        tag_objs: iterable of Tag model instances (should have .name)
        top_k: reserved for future use (currently returns single best)

    Returns:
        list of tag names (matching Tag.name) or None for no confident match.
    """
    texts = list(texts)
    tag_list = list(tag_objs)
    tag_names = [getattr(t, "name") for t in tag_list]
    if not texts or not tag_names:
        return [None] * len(texts)

    # Normalize tag names and prepare keyword lookup
    kw_map = {t.name.lower(): TAG_KEYWORDS.get(t.name, []) for t in tag_list}

    nlp = _load_nlp()
    # First attempt: keyword-based matching. For each text, count keyword
    # occurrences in the text (title+content combined when available). If any
    # tag has at least one match, pick the tag with the most matches.
    results_by_keyword: List[Optional[str]] = [None] * len(texts)
    for idx, text in enumerate(texts):
        if not text:
            continue
        tl = text.lower()
        best_tag = None
        best_count = 0
        # Use regex word-boundary matching to avoid substring false-positives
        for tname in tag_names:
            kws = kw_map.get(tname.lower(), [])
            if not kws:
                continue
            count = 0
            for kw in kws:
                if not kw:
                    continue
                # count word-boundary matches (case-insensitive)
                try:
                    count += len(re.findall(r"\b" + re.escape(kw.lower()) + r"\b", tl))
                except re.error:
                    # fallback to simple substring count if regex fails
                    count += tl.count(kw.lower())
            if count > best_count:
                best_count = count
                best_tag = tname
        if best_count > 0:
            results_by_keyword[idx] = best_tag

    # If keyword-based prediction produced results for all texts, return them
    if all((r is not None) for r in results_by_keyword):
        return results_by_keyword
    # Case: spaCy is available -> use vector/similarity when possible
    if nlp is not None:
        # Create spaCy docs for tag names once
        try:
            tag_docs = [nlp(name) for name in tag_names]
        except Exception:
            # If model can't parse text normally use make_doc
            tag_docs = [nlp.make_doc(name) for name in tag_names]

        results: List[Optional[str]] = []
        # Use pipe for batch processing; disable expensive components
        disable = [c for c in ("parser", "ner") if c in nlp.pipe_names]
        for doc_idx, doc in enumerate(nlp.pipe(texts, disable=disable)):
            # If keyword-based result exists for this text, prefer it
            if results_by_keyword[doc_idx] is not None:
                results.append(results_by_keyword[doc_idx])
                continue
            best_idx = None
            best_score = -1.0
            for i, tdoc in enumerate(tag_docs):
                try:
                    score = doc.similarity(tdoc)
                except Exception:
                    # If similarity isn't available (no vectors), use overlap
                    score = _token_overlap_score(doc.text, tdoc.text)
                if score > best_score:
                    best_score = score
                    best_idx = i

            # Heuristic threshold: if similarity/overlap is extremely low treat as None
            if best_idx is None:
                results.append(None)
            else:
                if best_score <= 0.05:  # very low confidence
                    results.append(None)
                else:
                    results.append(tag_names[best_idx])

        return results

    # Fallback: keyword/substring + token overlap
    lower_tag_names = [n.lower() for n in tag_names]
    results = []
    for text in texts:
        if not text:
            results.append(None)
            continue
        tl = text.lower()
        # Prefer direct substring match
        matched = None
        for i, tn in enumerate(lower_tag_names):
            if tn and tn in tl:
                matched = tag_names[i]
                break
        if matched:
            results.append(matched)
            continue

        # Use token overlap as a weak signal
        best_idx = None
        best_score = -1.0
        for i, tn in enumerate(tag_names):
            score = _token_overlap_score(text, tn)
            if score > best_score:
                best_score = score
                best_idx = i
        if best_idx is not None and best_score > 0.15:
            results.append(tag_names[best_idx])
        else:
            results.append(None)

    return results


def predict_tag(text: str, tag_objs: Optional[Iterable] = None) -> Optional[str]:
    """Convenience wrapper for single text.

    If tag_objs is None, caller is expected to pass available Tag instances.
    """
    if not text:
        return None
    return predict_tags_for_texts([text], tag_objs or [], top_k=1)[0]
