from __future__ import annotations

import re
from collections import Counter
from typing import Any


_WORD_RE = re.compile(r"[A-Za-zÀ-ỹ0-9_]+", re.UNICODE)

# Tiny mixed EN/VI stoplist (keep short; tool is just a helper).
_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "from", "as", "at", "by", "is", "are",
    "là", "và", "hoặc", "của", "trên", "trong", "cho", "với", "từ", "như", "tại", "bởi", "lúc", "khi", "được",
    "mình", "bạn", "tôi", "chúng", "ta", "này", "đó", "các", "một", "những",
}


def extract_keywords(text: str = "", top_k: int = 8) -> dict[str, Any]:
    if not text or not isinstance(text, str):
        return {"tool": "keywords", "keywords": []}

    tokens = [t.lower() for t in _WORD_RE.findall(text)]
    tokens = [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]
    counts = Counter(tokens)
    keywords = [w for w, _ in counts.most_common(max(1, int(top_k)))]
    return {"tool": "keywords", "keywords": keywords}

