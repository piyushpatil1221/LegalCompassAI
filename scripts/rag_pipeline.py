"""
LegalCompass AI - Step 3: RAG Pipeline & Legal Retriever
======================================================================
Provides the core retrieval-augmented generation pipeline for legal queries.

Classes:
  - LegalRAGRetriever: Interface to ChromaDB collections with multi-mode search
  - LegalRAGPipeline: Orchestrates query -> retrieve -> format flow

Search modes:
  - semantic_search(query, top_k, category_filter)
  - section_lookup(act, section_number)
  - hybrid_search(query, top_k)  [semantic + keyword re-ranking]
  - multi_collection_search(query, top_k)
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
REQUIRED = ["sentence_transformers", "chromadb"]
MISSING = [p for p in REQUIRED if not __import__("importlib").util.find_spec(p.replace("-", "_"))]
if MISSING:
    print(f"[ERROR] Missing packages: pip install {' '.join(MISSING)}")
    sys.exit(1)

from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_DIR  = Path(__file__).parent.parent
OUTPUT_DIR   = PROJECT_DIR / "BNS DATASET" / "output"
CHROMA_DIR   = OUTPUT_DIR / "chroma_db"
MODEL_NAME   = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"  # Trained for QA retrieval

COLLECTION_MAP = {
    "bare_acts":   "legalcompass_bare_acts",
    "case_docs":   "legalcompass_case_docs",
    "crime_stats": "legalcompass_crime_stats",
    "iltur":       "legalcompass_iltur",
}

ACT_ALIASES = {
    "BNS": "BNS", "bns": "BNS", "bharatiya nyaya sanhita": "BNS",
    "BNSS": "BNSS", "bnss": "BNSS", "bharatiya nagarik suraksha sanhita": "BNSS",
    "BSA": "BSA", "bsa": "BSA", "bharatiya sakshya adhiniyam": "BSA",
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
class SearchResult:
    def __init__(self, chunk_id: str, text: str, title: str, category: str,
                 score: float, metadata: Dict[str, Any]):
        self.chunk_id = chunk_id
        self.text     = text
        self.title    = title
        self.category = category
        self.score    = score
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "title":    self.title,
            "category": self.category,
            "score":    round(self.score, 4),
            "text":     self.text[:500] + ("..." if len(self.text) > 500 else ""),
            "text_full": self.text,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"SearchResult(id={self.chunk_id!r}, score={self.score:.3f}, title={self.title!r})"


# ---------------------------------------------------------------------------
# LegalRAGRetriever
# ---------------------------------------------------------------------------
class LegalRAGRetriever:
    """
    Interface to the ChromaDB legal corpus.
    Must call .connect() before searching, or use as context manager.
    """

    def __init__(self, chroma_dir: Path = CHROMA_DIR, model_name: str = MODEL_NAME):
        self.chroma_dir = chroma_dir
        self.model_name = model_name
        self._client: Optional[chromadb.ClientAPI] = None
        self._collections: Dict[str, Any] = {}
        self._model: Optional[SentenceTransformer] = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self) -> "LegalRAGRetriever":
        if not self.chroma_dir.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {self.chroma_dir}. "
                "Run embed_and_index.py first."
            )
        print(f"[RAG] Connecting to ChromaDB: {self.chroma_dir}")
        self._client = chromadb.PersistentClient(path=str(self.chroma_dir))

        print(f"[RAG] Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name)

        for key, col_name in COLLECTION_MAP.items():
            try:
                self._collections[key] = self._client.get_collection(col_name)
                count = self._collections[key].count()
                print(f"[RAG]   {col_name}: {count:,} vectors")
            except Exception as e:
                print(f"[RAG]   WARNING: Collection {col_name} not found: {e}")

        return self

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        pass

    # Legal synonym map for query expansion (Indian criminal law focused)
    _LEGAL_SYNONYMS: Dict[str, List[str]] = {
        "murder":           ["homicide", "culpable homicide", "killing", "death", "manslaughter"],
        "punishment":       ["penalty", "sentence", "imprisonment", "fine", "rigorous imprisonment"],
        "bail":             ["anticipatory bail", "regular bail", "custody", "remand", "interim bail", "default bail"],
        "rape":             ["sexual assault", "sexual offence", "gang rape", "molestation"],
        "theft":            ["robbery", "dacoity", "snatching", "burglary", "extortion"],
        "evidence":         ["proof", "witness", "testimony", "document", "confession", "deposition"],
        "accused":          ["defendant", "offender", "convict", "undertrial", "suspect"],
        "court":            ["tribunal", "magistrate", "judge", "sessions court", "high court"],
        "section":          ["provision", "clause", "article", "sub-section"],
        "offence":          ["crime", "violation", "act", "cognizable offence", "non-cognizable"],
        "arrest":           ["detention", "apprehension", "custody", "warrant"],
        "fir":              ["first information report", "complaint", "chargesheet", "challan"],
        "investigation":    ["inquiry", "probe", "chargesheet", "police report"],
        "acquittal":        ["discharge", "exoneration", "not guilty"],
        "conviction":       ["guilty", "sentenced", "found guilty", "imprisonment"],
        "appeal":           ["revision", "writ", "petition", "challenge"],
        "assault":          ["hurt", "grievous hurt", "bodily harm", "attack", "battery"],
    }
    _LEGAL_STOPWORDS = {"the", "a", "an", "and", "or", "of", "in", "is", "to", "for", "under", "with", "by", "on", "at", "that", "this", "which", "what", "how"}

    # Intent → preferred collection mapping
    _INTENT_PATTERNS: Dict[str, List[str]] = {
        "bare_acts":   [r"\b(BNS|BNSS|BSA)\b", r"section\s*\d+", r"provision", r"act says", r"defined as", r"meaning of", r"definition"],
        "crime_stats": [r"statistic", r"district", r"state.wise", r"NCRB", r"rate", r"cases reported", r"how many", r"total.*cases", r"trend"],
        "case_docs":   [r"judgment", r"case", r"accused.*convicted", r"court.*held", r"sentenced", r"acquitt", r"appeal", r"petitioner"],
        "iltur":       [r"bail.*granted", r"bail.*denied", r"predict", r"outcome", r"likelihood", r"will.*get bail", r"chances"],
    }

    def _classify_intent(self, query: str) -> Optional[str]:
        """Returns best-matching collection key, or None to search all."""
        ql = query.lower()
        scores = {cat: sum(1 for p in patterns if re.search(p, ql, re.IGNORECASE))
                  for cat, patterns in self._INTENT_PATTERNS.items()}
        best_cat, best_score = max(scores.items(), key=lambda x: x[1])
        # Only override if clearly dominant; ties → search all
        if best_score >= 2:
            return best_cat
        return None

    def _expand_query(self, query: str) -> str:
        """Append legal synonyms to query for better recall."""
        ql = query.lower()
        extras = []
        for term, synonyms in self._LEGAL_SYNONYMS.items():
            if term in ql:
                extras.extend(synonyms)
        if extras:
            return query + " " + " ".join(extras)
        return query

    def _embed(self, text: str) -> List[float]:
        return self._model.encode(text, show_progress_bar=False, normalize_embeddings=True).tolist()

    def _chroma_results_to_list(self, results: Dict, source_category: str) -> List[SearchResult]:
        out = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return out
        ids       = results["ids"][0]
        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results.get("distances", [[0.0] * len(ids)])[0]

        # Normalize scores within this batch so all collections compete on same scale
        raw_scores = [max(0.0, 1.0 - d) for d in distances]
        min_s, max_s = min(raw_scores), max(raw_scores)
        score_range = max_s - min_s if max_s > min_s else 1.0

        for i, chunk_id in enumerate(ids):
            meta  = metas[i] if metas else {}
            # Min-max normalize to [0.5, 1.0] — preserves relative order, lifts fair competition
            norm_score = 0.5 + 0.5 * (raw_scores[i] - min_s) / score_range
            out.append(SearchResult(
                chunk_id=chunk_id,
                text=docs[i],
                title=meta.get("title", ""),
                category=meta.get("category", source_category),
                score=norm_score,
                metadata=meta,
            ))
        return out

    # ------------------------------------------------------------------
    # Search modes
    # ------------------------------------------------------------------
    @staticmethod
    def _text_fingerprint(text: str) -> str:
        """First 80 chars of normalized text — cheap near-duplicate key."""
        return re.sub(r"\s+", " ", text.strip().lower())[:80]

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Dense vector similarity search with near-duplicate filtering.
        category_filter: one of 'bare_acts', 'case_docs', 'crime_stats', 'iltur', or None (all)
        """
        embedding = self._embed(query)
        results: List[SearchResult] = []

        categories = [category_filter] if category_filter else list(COLLECTION_MAP.keys())

        for cat in categories:
            col = self._collections.get(cat)
            if col is None:
                continue
            try:
                res = col.query(
                    query_embeddings=[embedding],
                    n_results=min(top_k, col.count()),
                    include=["documents", "metadatas", "distances"],
                )
                results.extend(self._chroma_results_to_list(res, cat))
            except Exception as e:
                print(f"[RAG] Warning: search failed on {cat}: {e}")

        # Sort by score descending, deduplicate near-identical chunks, return top_k
        results.sort(key=lambda r: r.score, reverse=True)
        seen, deduped = set(), []
        for r in results:
            fp = self._text_fingerprint(r.text)
            if fp not in seen:
                seen.add(fp)
                deduped.append(r)
        return deduped[:top_k]

    def section_lookup(self, act: str, section_number: str) -> Optional[SearchResult]:
        """
        Exact lookup of a bare-act section by act name and section number.
        e.g. section_lookup('BNS', '103')
        """
        col = self._collections.get("bare_acts")
        if col is None:
            return None

        normalized_act = ACT_ALIASES.get(act.strip(), act.strip().upper())
        # Normalize section number: strip leading zeros variance, handle 'S.103', '103A' etc.
        sec_clean = re.sub(r"[^\w]", "", str(section_number).strip())  # remove dots/spaces
        sec_num   = re.match(r"\d+", sec_clean)  # grab numeric part only
        sec_padded = (sec_num.group(0) if sec_num else sec_clean).zfill(3)
        chunk_id   = f"{normalized_act}_S{sec_padded}_C01"

        try:
            res = col.get(ids=[chunk_id], include=["documents", "metadatas"])
            if res and res["ids"]:
                meta = res["metadatas"][0] if res["metadatas"] else {}
                return SearchResult(
                    chunk_id=chunk_id,
                    text=res["documents"][0],
                    title=meta.get("title", f"{normalized_act} S{section_number}"),
                    category="bare_acts",
                    score=1.0,
                    metadata=meta,
                )
        except Exception as e:
            print(f"[RAG] section_lookup failed: {e}")
        return None

    @staticmethod
    def _rrf_merge(lists: List[List["SearchResult"]], k: int = 60) -> List["SearchResult"]:
        """Reciprocal Rank Fusion — merges multiple ranked lists, ignores raw score scale."""
        scores: Dict[str, float] = {}
        items: Dict[str, "SearchResult"] = {}
        for lst in lists:
            for rank, result in enumerate(lst, 1):
                scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (k + rank)
                items[result.chunk_id] = result
        merged = sorted(items.values(), key=lambda r: scores[r.chunk_id], reverse=True)
        # Normalize RRF scores to [0,1] for display consistency
        if merged:
            max_s = scores[merged[0].chunk_id]
            for r in merged:
                r.score = scores[r.chunk_id] / max_s
        return merged

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        alpha: float = 0.65,
    ) -> List["SearchResult"]:
        """
        Hybrid: semantic (with query expansion) + keyword re-ranking fused via RRF.
        """
        # Step 1: Auto-detect intent to narrow collection if not already filtered
        effective_filter = category_filter or self._classify_intent(query)

        # Step 2: Expand query for semantic recall
        expanded_query = self._expand_query(query)
        pool_k = min(top_k * 8, 80)
        semantic_results = self.semantic_search(expanded_query, top_k=pool_k, category_filter=effective_filter)

        # Step 3: Keyword re-ranking list (BM25-style)
        raw_terms = re.sub(r"[^\w\s]", " ", query.lower()).split()
        query_terms = [t for t in raw_terms if len(t) > 2 and t not in self._LEGAL_STOPWORDS]
        section_patterns = re.findall(r"(?:section|sec\.?)\s*\d+|\b(?:BNS|BNSS|BSA)\b", query, re.IGNORECASE)

        def keyword_score(text: str, title: str) -> float:
            text_lower, title_lower = text.lower(), title.lower()
            if not query_terms:
                return 0.0
            tf_hits  = sum(text_lower.count(t) for t in query_terms)
            tf_score = min(tf_hits / (max(len(query_terms), 1) * 4.0), 1.0)
            title_bonus   = sum(1 for t in query_terms if t in title_lower) / max(len(query_terms), 1) * 0.3
            section_bonus = sum(0.2 for p in section_patterns if p.lower() in text_lower)
            return min(tf_score + title_bonus + section_bonus, 1.0)

        # Build keyword-ranked list from same pool
        keyword_ranked = sorted(semantic_results, key=lambda r: keyword_score(r.text, r.title), reverse=True)

        # Step 4: RRF-merge semantic + keyword lists for robust final ranking
        merged = self._rrf_merge([semantic_results[:pool_k], keyword_ranked[:pool_k]])
        return merged[:top_k]

    def multi_collection_search(
        self,
        query: str,
        top_k_per_collection: int = 3,
    ) -> Dict[str, List[SearchResult]]:
        """
        Search each collection independently and return results per category.
        Useful for showing diverse results across bare acts, cases, stats, IL-TUR.
        """
        embedding = self._embed(query)
        out: Dict[str, List[SearchResult]] = {}

        for cat, col in self._collections.items():
            try:
                res = col.query(
                    query_embeddings=[embedding],
                    n_results=min(top_k_per_collection, col.count()),
                    include=["documents", "metadatas", "distances"],
                )
                out[cat] = self._chroma_results_to_list(res, cat)
            except Exception as e:
                print(f"[RAG] multi_collection_search failed for {cat}: {e}")
                out[cat] = []

        return out


# ---------------------------------------------------------------------------
# LegalRAGPipeline
# ---------------------------------------------------------------------------
class LegalRAGPipeline:
    """
    High-level pipeline: query -> retrieve -> format response.
    In retrieval-only mode (no LLM), returns structured retrieved context.
    """

    def __init__(self, retriever: LegalRAGRetriever):
        self.retriever = retriever

    def query(
        self,
        question: str,
        top_k: int = 5,
        search_mode: str = "hybrid",  # "semantic" | "hybrid" | "multi"
        category_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main query entry-point.
        Returns: {question, retrieved_chunks, answer_mode, elapsed_ms}
        """
        t0 = time.time()

        # Detect section lookup intent (e.g. "BNS section 103", "BNSS s.45")
        section_match = re.search(
            r"\b(BNS|BNSS|BSA)\b.*?[Ss]ec(?:tion)?\.?\s*(\d+)|[Ss]ec(?:tion)?\.?\s*(\d+).*?\b(BNS|BNSS|BSA)\b",
            question, re.IGNORECASE
        )
        if section_match:
            # Handle both "BNS section 103" and "section 103 of BNS" patterns
            act = (section_match.group(1) or section_match.group(4)).upper()
            sec = (section_match.group(2) or section_match.group(3))
            result = self.retriever.section_lookup(act, sec)
            if result:
                # Also fetch related chunks for context
                extra = self._retrieve(question, top_k - 1, search_mode, category_filter)
                chunks = [result] + [c for c in extra if c.chunk_id != result.chunk_id]
                mode = "section_lookup"
            else:
                chunks = self._retrieve(question, top_k, search_mode, category_filter)
                mode = search_mode
        else:
            chunks = self._retrieve(question, top_k, search_mode, category_filter)
            mode = search_mode

        elapsed_ms = round((time.time() - t0) * 1000)

        # Format answer (retrieval-only)
        answer = self._format_retrieval_answer(question, chunks)

        return {
            "question": question,
            "answer": answer,
            "answer_mode": "retrieval_only",
            "search_mode": mode,
            "retrieved_chunks": [c.to_dict() for c in chunks],
            "retrieved_count": len(chunks),
            "elapsed_ms": elapsed_ms,
        }

    def _retrieve(self, q, top_k, mode, category_filter):
        if mode == "multi":
            all_results = self.retriever.multi_collection_search(q, top_k_per_collection=top_k)
            return [r for results in all_results.values() for r in results]
        elif mode == "hybrid":
            return self.retriever.hybrid_search(q, top_k=top_k, category_filter=category_filter)
        else:
            return self.retriever.semantic_search(q, top_k=top_k, category_filter=category_filter)

    def _format_retrieval_answer(self, question: str, chunks: List[SearchResult]) -> str:
        if not chunks:
            return "No relevant legal information found for your query."

        lines = [f"Based on the legal corpus, here are the most relevant references for:\n'{question}'\n"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"--- [{i}] {chunk.title} (Score: {chunk.score:.3f}) ---")
            lines.append(f"Category: {chunk.category}")
            preview = chunk.text[:1000].strip()
            if len(chunk.text) > 1000:
                preview += "..."
            lines.append(preview)
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI test mode
# ---------------------------------------------------------------------------
def run_cli():
    print("=" * 70)
    print("  LegalCompass AI -- RAG Pipeline CLI (Retrieval-Only Mode)")
    print("=" * 70)

    retriever = LegalRAGRetriever()
    retriever.connect()
    pipeline  = LegalRAGPipeline(retriever)

    test_queries = [
        "What are the punishments for murder under BNS Section 103?",
        "BNSS section 167 bail provisions",
        "rape victim statistics district wise",
        "bail granted in murder cases prediction",
        "What is culpable homicide not amounting to murder?",
    ]

    print("\n--- Running test queries ---\n")
    for q in test_queries:
        print(f"\nQ: {q}")
        result = pipeline.query(q, top_k=3, search_mode="hybrid")
        print(f"   Mode: {result['search_mode']} | Retrieved: {result['retrieved_count']} | {result['elapsed_ms']}ms")
        for chunk in result["retrieved_chunks"][:2]:
            print(f"   [{chunk['score']:.3f}] {chunk['title']}")
            print(f"           {chunk['text'][:150]}...")
        print()


if __name__ == "__main__":
    run_cli()
