"""
LegalCompass AI - Step 2: Vector Embedding & ChromaDB Indexing
======================================================================
Generates sentence-transformer embeddings for all corpus chunks and
stores them in a persistent ChromaDB vector database.

Collections created:
  - legalcompass_bare_acts  (1,057 chunks  - ALL)
  - legalcompass_case_docs  (19,834 chunks - ALL)
  - legalcompass_crime_stats(14,799 chunks - ALL)
  - legalcompass_iltur      (50,000 chunks - SAMPLED, stratified by task)

Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim, CPU-friendly)
Output: BNS DATASET/output/chroma_db/
"""

import json
import os
import sys
import random
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
REQUIRED_PACKAGES = ["sentence_transformers", "chromadb"]
MISSING = []
for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        MISSING.append(pkg)

if MISSING:
    print("\n[ERROR] Missing required packages. Run:")
    print(f"  pip install {' '.join(MISSING)}")
    sys.exit(1)

from sentence_transformers import SentenceTransformer
import chromadb


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_DIR   = Path(__file__).parent.parent
OUTPUT_DIR    = PROJECT_DIR / "BNS DATASET" / "output"
CHUNKS_DIR    = OUTPUT_DIR / "chunks"
CHROMA_DIR    = OUTPUT_DIR / "chroma_db"
REPORT_PATH   = OUTPUT_DIR / "embeddings_report.json"

MODEL_NAME    = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE    = 256
ILTUR_SAMPLE  = 50_000       # max chunks to sample from iltur_chunks.json
RANDOM_SEED   = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_chunks(path: Path) -> List[Dict[str, Any]]:
    print(f"    Loading {path.name} ({path.stat().st_size / 1_048_576:.1f} MB)...", flush=True)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sample_iltur(chunks: List[Dict[str, Any]], n: int, seed: int) -> List[Dict[str, Any]]:
    """Stratified sample across task_type so all 8 IL-TUR tasks are represented."""
    by_task: Dict[str, List] = defaultdict(list)
    for c in chunks:
        task = c.get("metadata", {}).get("task_type", "other")
        by_task[task].append(c)

    per_task = n // max(len(by_task), 1)
    sampled = []
    rng = random.Random(seed)

    for task, task_chunks in sorted(by_task.items()):
        take = min(per_task, len(task_chunks))
        sampled.extend(rng.sample(task_chunks, take))
        print(f"      Task [{task}]: {len(task_chunks):,} available -> sampled {take:,}")

    # top-up if total < n (due to rounding)
    flat_keys = set(id(c) for c in sampled)
    remaining = [c for c in chunks if id(c) not in flat_keys]
    if len(sampled) < n and remaining:
        extra = min(n - len(sampled), len(remaining))
        sampled.extend(rng.sample(remaining, extra))

    rng.shuffle(sampled)
    return sampled[:n]


def embed_and_upsert(
    collection,
    chunks: List[Dict[str, Any]],
    model: SentenceTransformer,
    batch_size: int = BATCH_SIZE,
) -> int:
    """Embed chunks in batches and upsert into a ChromaDB collection. Returns count."""
    total = len(chunks)
    upserted = 0

    for batch_start in range(0, total, batch_size):
        batch = chunks[batch_start : batch_start + batch_size]

        ids       = [c["chunk_id"]  for c in batch]
        texts     = [c["text"]      for c in batch]

        # Build clean metadata (ChromaDB only accepts str/int/float/bool)
        metadatas = []
        for c in batch:
            raw_meta = c.get("metadata", {})
            clean = {"title": c.get("title", ""), "category": c.get("corpus_category", "")}
            for k, v in raw_meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                elif isinstance(v, list):
                    clean[k] = ", ".join(str(x) for x in v)
                else:
                    clean[k] = str(v)
            metadatas.append(clean)

        embeddings = model.encode(texts, show_progress_bar=False, batch_size=64).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        upserted += len(batch)
        pct = 100 * upserted / total
        bar  = "#" * int(pct // 5) + "." * (20 - int(pct // 5))
        print(f"\r      [{bar}] {upserted:>7,}/{total:,} ({pct:5.1f}%)", end="", flush=True)

    print()  # newline after progress bar
    return upserted


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  LegalCompass AI -- Step 2: Vector Embedding & ChromaDB Indexing")
    print("=" * 70)

    # 1. Load embedding model
    print(f"\n[1/6] Loading embedding model: {MODEL_NAME}")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_embedding_dimension() if hasattr(model, 'get_embedding_dimension') else model.get_sentence_embedding_dimension()
    print(f"      Model loaded in {time.time() - t0:.1f}s  (dim={dim})")

    # 2. Initialise ChromaDB
    print(f"\n[2/6] Initialising ChromaDB at: {CHROMA_DIR}")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 3. Load chunks
    print("\n[3/6] Loading chunk files...")
    bare_chunks   = load_chunks(CHUNKS_DIR / "bare_acts_chunks.json")
    case_chunks   = load_chunks(CHUNKS_DIR / "case_docs_chunks.json")
    stats_chunks  = load_chunks(CHUNKS_DIR / "crime_stats_chunks.json")

    print(f"    Loading iltur_chunks.json -- sampling {ILTUR_SAMPLE:,} chunks stratified by task...")
    iltur_all     = load_chunks(CHUNKS_DIR / "iltur_chunks.json")
    iltur_chunks  = sample_iltur(iltur_all, ILTUR_SAMPLE, RANDOM_SEED)
    del iltur_all   # free memory

    # 4. Create / get collections
    print("\n[4/6] Creating ChromaDB collections...")
    def get_col(name: str):
        try:
            col = client.create_collection(name=name, metadata={"hnsw:space": "cosine"})
            print(f"      Created collection: {name}")
        except Exception:
            col = client.get_collection(name=name)
            print(f"      Collection exists, reusing: {name}")
        return col

    col_bare   = get_col("legalcompass_bare_acts")
    col_case   = get_col("legalcompass_case_docs")
    col_stats  = get_col("legalcompass_crime_stats")
    col_iltur  = get_col("legalcompass_iltur")

    # 5. Embed & upsert
    report = {"model": MODEL_NAME, "collections": {}}

    def run(name: str, col, chunks: List[Dict[str, Any]]):
        print(f"\n[5/6] Embedding & indexing: {name} ({len(chunks):,} chunks)")
        t = time.time()
        n = embed_and_upsert(col, chunks, model)
        elapsed = time.time() - t
        report["collections"][name] = {
            "chunks_indexed": n,
            "elapsed_seconds": round(elapsed, 1),
            "chunks_per_second": round(n / elapsed, 1) if elapsed > 0 else 0,
        }
        elapsed_safe = max(elapsed, 0.001)
        print(f"      OK  {n:,} chunks indexed in {elapsed:.1f}s ({n/elapsed_safe:.0f} chunks/s)")

    run("legalcompass_bare_acts",   col_bare,  bare_chunks)
    run("legalcompass_case_docs",   col_case,  case_chunks)
    run("legalcompass_crime_stats", col_stats, stats_chunks)
    run("legalcompass_iltur",       col_iltur, iltur_chunks)

    # 6. Save report
    print(f"\n[6/6] Saving embeddings report to {REPORT_PATH}")
    report["total_chunks_indexed"] = sum(
        v["chunks_indexed"] for v in report["collections"].values()
    )
    report["chroma_db_path"] = str(CHROMA_DIR)
    report["iltur_sample_size"] = ILTUR_SAMPLE
    report["status"] = "complete"

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("  EMBEDDING SUMMARY")
    print("=" * 70)
    for name, info in report["collections"].items():
        print(f"  {name:<35}: {info['chunks_indexed']:>7,} chunks  ({info['elapsed_seconds']}s)")
    print(f"  {'TOTAL':<35}: {report['total_chunks_indexed']:>7,} chunks")
    print(f"\n  ChromaDB stored at: {CHROMA_DIR}")
    print(f"  Report saved at:    {REPORT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
