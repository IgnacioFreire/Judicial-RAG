"""Cross-encoder rerank. The model loads on the first slow retrieval."""

import logging

from config.embeddings import RERANK_MODEL

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None


def score(question: str, texts: list[str]) -> list[float]:
    """Return one relevance score per text. Higher means closer to the question."""
    if not texts:
        return []
    tokenizer, model = _load()
    import torch

    pairs = [[question, text] for text in texts]
    encoded = tokenizer(
        pairs,
        padding=True,
        truncation=True,
        return_tensors="pt",
    )
    with torch.no_grad():
        logits = model(**encoded).logits.view(-1)
    return [float(value) for value in logits.tolist()]


def _load():
    """Load the multilingual cross-encoder once."""
    global _tokenizer, _model
    if _model is None or _tokenizer is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(RERANK_MODEL)
        _model.eval()
        logger.debug("Reranker loaded: %s", RERANK_MODEL)
    return _tokenizer, _model
