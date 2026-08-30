"""Context retrieval over a local knowledge corpus.

Offline (default) this is a deterministic keyword retriever over the markdown files in
factory/knowledge/. The interface is the seam: swap LocalRetriever for a Vertex AI Search
retriever indexed over your GitLab repos + Confluence spaces + tool docs, and every skill
that calls retrieve() keeps working unchanged. Context precision over volume: it returns
the few relevant passages, not the whole corpus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"
_WORD = re.compile(r"[a-z0-9]+")


@dataclass
class Passage:
    source: str          # file it came from
    heading: str         # the section heading
    text: str
    score: float


def _tokens(s: str) -> set[str]:
    return set(_WORD.findall(s.lower()))


def _chunks(md: str, source: str) -> list[tuple[str, str]]:
    """Split a markdown doc into (heading, body) chunks on '## ' headings."""
    parts = re.split(r"^##\s+", md, flags=re.MULTILINE)
    out: list[tuple[str, str]] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        line, _, body = part.partition("\n")
        out.append((line.strip(), body.strip() or line.strip()))
    return out


class LocalRetriever:
    def __init__(self, root: Path = KNOWLEDGE_DIR):
        self.root = root
        self._passages: list[Passage] = []
        self._load()

    def _load(self) -> None:
        for path in sorted(self.root.rglob("*.md")):
            rel = str(path.relative_to(self.root))
            for heading, body in _chunks(path.read_text(), rel):
                self._passages.append(Passage(rel, heading, body, 0.0))

    def retrieve(self, query: str, k: int = 4) -> list[Passage]:
        q = _tokens(query)
        if not q:
            return []
        scored: list[Passage] = []
        for p in self._passages:
            overlap = q & _tokens(p.heading + " " + p.text)
            if overlap:
                score = len(overlap) / len(q)
                scored.append(Passage(p.source, p.heading, p.text, round(score, 3)))
        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[:k]
