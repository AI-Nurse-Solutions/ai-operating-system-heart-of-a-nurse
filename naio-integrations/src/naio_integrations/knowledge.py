"""Knowledge-retrieval reference adapter (pattern: infiniflow/ragflow).

Governed retrieval, not "chat with your documents": every answer shows its
exact source and effective dates, separates policy from research and local
practice, warns when a policy is expired or from another jurisdiction, and
refuses to answer when no indexed source supports the question.
"""

from __future__ import annotations

from datetime import date

from .contract import KnowledgeAnswer, KnowledgeRetrievalInterface, KnowledgeSource

STOPWORDS = {
    "a", "an", "and", "are", "at", "be", "by", "can", "do", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "our", "the", "this", "to",
    "we", "what", "when", "where", "which", "who", "why", "with",
}


class GovernedKnowledge(KnowledgeRetrievalInterface):
    """Deterministic keyword retriever with governance metadata surfaced."""

    def __init__(self, home_jurisdiction: str = "US"):
        self.home_jurisdiction = home_jurisdiction
        self._sources: dict[str, list[KnowledgeSource]] = {}

    def index(self, sources) -> int:
        count = 0
        for source in sources:
            self._sources.setdefault(source.tenant, []).append(source)
            count += 1
        return count

    def source(self, tenant: str, source_id: str) -> KnowledgeSource | None:
        """Look up one indexed source without crossing tenant boundaries."""
        for source in self._sources.get(tenant, []):
            if source.source_id == source_id:
                return source
        return None

    def retrieve(self, tenant: str, query: str, today: str) -> KnowledgeAnswer:
        terms = {
            term for term in query.lower().split() if term and term not in STOPWORDS
        }
        current = date.fromisoformat(today)
        passages = []
        warnings: list[str] = []
        for source in self._sources.get(tenant, []):
            haystack = f"{source.title} {source.content}".lower()
            matched = {term for term in terms if term in haystack}
            if not matched:
                continue
            passage_warnings = []
            if source.expires_date and date.fromisoformat(source.expires_date) < current:
                passage_warnings.append(
                    f"EXPIRED: {source.source_id} lapsed on {source.expires_date}; "
                    "verify the current version before relying on it."
                )
            if source.jurisdiction != self.home_jurisdiction:
                passage_warnings.append(
                    f"JURISDICTION: {source.source_id} applies to "
                    f"{source.jurisdiction}, not {self.home_jurisdiction}."
                )
            warnings.extend(passage_warnings)
            passages.append(
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "doc_type": source.doc_type,
                    "effective_date": source.effective_date,
                    "expires_date": source.expires_date,
                    "jurisdiction": source.jurisdiction,
                    "excerpt": source.content[:280],
                    "matched_terms": sorted(matched),
                    "warnings": tuple(passage_warnings),
                }
            )
        if not passages:
            return KnowledgeAnswer(
                passages=(),
                warnings=(),
                refused=True,
                refusal_reason=(
                    "No indexed source supports this question; refusing to "
                    "answer without grounding."
                ),
            )
        order = {"policy": 0, "local_practice": 1, "research": 2}
        passages.sort(
            key=lambda passage: (
                order.get(passage["doc_type"], 3),
                -len(passage["matched_terms"]),
            )
        )
        conflicting = {p["doc_type"] for p in passages}
        if "policy" in conflicting and len(conflicting) > 1:
            warnings.append(
                "MIXED EVIDENCE: results include policy alongside research or "
                "local practice; policy governs practice, research informs it."
            )
        return KnowledgeAnswer(passages=tuple(passages), warnings=tuple(warnings))
