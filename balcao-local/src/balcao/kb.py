"""Runbook corpus: load .md files, rank by word overlap (no embeddings)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from balcao.models import DocHit

_WORD = re.compile(r"[a-zà-ú0-9]+")

STOPWORDS = frozenset(
    {
        "a", "o", "e", "de", "da", "do", "das", "dos", "em", "na", "no",
        "nas", "nos", "um", "uma", "uns", "umas", "com", "por", "para",
        "sem", "sob", "que", "qual", "quais", "meu", "minha", "meus",
        "seu", "sua", "hoje", "aqui", "isso", "esta", "este", "como",
    }
)


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in STOPWORDS}


@dataclass(frozen=True, slots=True)
class Runbook:
    """One parsed runbook file."""

    doc_id: str
    text: str


def load_kb(kb_dir: Path) -> list[Runbook]:
    """Load every .md runbook; first line declares `# id: <doc_id>`."""
    books: list[Runbook] = []
    for path in sorted(kb_dir.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        doc_id = lines[0].removeprefix("# id:").strip() if lines else path.stem
        books.append(Runbook(doc_id=doc_id, text="\n".join(lines[1:])))
    return books


@dataclass(frozen=True, slots=True)
class Retriever:
    """Keyword retriever with precomputed token sets."""

    books: tuple[Runbook, ...] = field(default=())
    _index: tuple[frozenset[str], ...] = field(default=(), repr=False)

    @classmethod
    def build(cls, books: list[Runbook]) -> Retriever:
        """Precompute token sets once; the retriever stays immutable."""
        return cls(
            books=tuple(books),
            _index=tuple(
                frozenset(_tokens(b.text) | _tokens(b.doc_id.replace("-", " ")))
                for b in books
            ),
        )

    def search(self, query: str, top_k: int = 2) -> list[DocHit]:
        """Rank by overlap ratio; empty list when nothing overlaps."""
        qtokens = _tokens(query)
        hits: list[DocHit] = []
        for book, btokens in zip(self.books, self._index, strict=True):
            overlap = len(qtokens & btokens)
            if overlap:
                hits.append(
                    DocHit(book.doc_id, book.text, overlap / len(qtokens))
                )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]


def default_retriever() -> Retriever:
    """Build over the shipped kb/ directory next to this package."""
    kb_dir = Path(__file__).resolve().parents[2] / "kb"
    return Retriever.build(load_kb(kb_dir))
