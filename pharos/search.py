"""Small BM25 index over event text. Swap for VAST vector search when the VAST environment is available."""
from __future__ import annotations

import math
import re
from collections import Counter

_tok = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return _tok.findall(text.lower())


class Index:
    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.toks = [tokens(d["text"]) for d in docs]
        self.avg = (sum(len(t) for t in self.toks) / len(self.toks)) if self.toks else 0.0
        df = Counter()
        for t in self.toks:
            df.update(set(t))
        n = len(self.toks)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def search(self, query: str, top: int = 5) -> list[dict]:
        q = tokens(query)
        scored = []
        for doc, t in zip(self.docs, self.toks):
            tf = Counter(t)
            s = 0.0
            for w in q:
                if w in tf:
                    s += self.idf.get(w, 0) * tf[w] * (self.k1 + 1) / (
                        tf[w] + self.k1 * (1 - self.b + self.b * len(t) / (self.avg or 1)))
            if s > 0:
                scored.append((s, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [dict(d, score=round(s, 3)) for s, d in scored[:top]]
