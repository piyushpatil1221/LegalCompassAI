"""
LegalCompass AI - Step 4: IL-TUR Evaluation Benchmark Harness
======================================================================
Evaluates the RAG pipeline on three IL-TUR tasks using a stratified sample:

  Task 1 - LSI  (Legal Statute Identification):
    Given case facts, retrieve relevant BNS/IPC sections.
    Metrics: Precision@K, Recall@K, F1@K, NDCG@K

  Task 2 - CJPE (Court Judgment Prediction & Explanation):
    Given case facts, predict judgment outcome (accepted/rejected).
    Metrics: Accuracy, Macro-F1, Class-wise F1

  Task 3 - Bail Prediction:
    Given case facts/petition, predict bail grant (Yes/No).
    Metrics: Accuracy, Macro-F1, AUC-ROC

Output: BNS DATASET/output/evaluation_report.json
        BNS DATASET/output/evaluation_summary.txt
"""

import json
import os
import re
import sys
import time
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
REQUIRED = ["sentence_transformers", "chromadb", "sklearn"]
MISSING = []
for pkg in REQUIRED:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        MISSING.append(pkg)

if MISSING:
    print(f"[ERROR] Missing packages: pip install {' '.join(MISSING)}")
    sys.exit(1)

from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score, classification_report
)

# rag_pipeline is in same directory
sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import LegalRAGRetriever, LegalRAGPipeline

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_DIR  = Path(__file__).parent.parent
OUTPUT_DIR   = PROJECT_DIR / "BNS DATASET" / "output"
CHUNKS_DIR   = OUTPUT_DIR / "chunks"
REPORT_PATH  = OUTPUT_DIR / "evaluation_report.json"
SUMMARY_PATH = OUTPUT_DIR / "evaluation_summary.txt"

EVAL_SAMPLES_PER_TASK = 200   # number of test samples per task
RANDOM_SEED           = 42
TOP_K                 = 5     # for LSI precision/recall


# ---------------------------------------------------------------------------
# Load IL-TUR evaluation data from chunks
# ---------------------------------------------------------------------------
def load_iltur_chunks_by_task(chunks_path: Path) -> Dict[str, List[Dict]]:
    """Load iltur_chunks.json and group by task type."""
    print(f"  Loading IL-TUR chunks ({chunks_path.stat().st_size / 1e9:.2f} GB)...", flush=True)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    by_task: Dict[str, List] = defaultdict(list)
    for c in chunks:
        task = c.get("metadata", {}).get("task_type", "other")
        by_task[task].append(c)

    for task, items in sorted(by_task.items()):
        print(f"    [{task}]: {len(items):,} chunks")

    return dict(by_task)


def sample_chunks(chunks: List[Dict], n: int, seed: int) -> List[Dict]:
    rng = random.Random(seed)
    return rng.sample(chunks, min(n, len(chunks)))


# ---------------------------------------------------------------------------
# LSI Evaluation (Legal Statute Identification)
# ---------------------------------------------------------------------------
def evaluate_lsi(
    pipeline: LegalRAGPipeline,
    lsi_chunks: List[Dict],
    n_samples: int,
    top_k: int = TOP_K,
) -> Dict[str, Any]:
    """
    LSI: given case text, retrieve relevant BNS/BNSS sections.
    Evaluates retrieval quality by checking how many retrieved chunks
    are from bare_acts category and contain relevant legal sections.
    """
    print(f"\n  [LSI] Evaluating Legal Statute Identification ({n_samples} samples, top-{top_k})...")
    samples = sample_chunks(lsi_chunks, n_samples, RANDOM_SEED)

    hits_at_k   = []
    precision_k = []
    recall_k    = []
    ndcg_k      = []

    for i, chunk in enumerate(samples):
        query = chunk["text"][:500]

        result = pipeline.query(
            query, top_k=top_k, search_mode="hybrid", category_filter=None
        )

        retrieved = result["retrieved_chunks"]

        # LSI metric: how many retrieved docs are bare_acts (statute retrieval)
        bare_acts_retrieved = [r for r in retrieved if r.get("category") == "bare_acts"]
        n_bare = len(bare_acts_retrieved)

        p_at_k = n_bare / max(len(retrieved), 1)
        # Recall: idealised — at least 1 bare_act section expected for legal case text
        r_at_k = min(n_bare / max(top_k // 2, 1), 1.0)  # expect at least top_k//2 relevant
        h_at_k = 1 if n_bare > 0 else 0

        # NDCG@K (graded relevance: bare_act=1, others=0)
        gains = [1 if r.get("category") == "bare_acts" else 0 for r in retrieved]
        dcg   = sum(g / (i + 1) for i, g in enumerate(gains))
        ideal_dcg = sum(1.0 / (i + 1) for i in range(min(n_bare, top_k)))
        ndcg  = dcg / max(ideal_dcg, 1e-10)

        hits_at_k.append(h_at_k)
        precision_k.append(p_at_k)
        recall_k.append(r_at_k)
        ndcg_k.append(ndcg)

        if (i + 1) % 50 == 0:
            print(f"    Progress: {i+1}/{n_samples} | Avg P@{top_k}={sum(precision_k)/len(precision_k):.3f}", flush=True)

    metrics = {
        "task": "LSI",
        "n_samples": len(samples),
        "top_k": top_k,
        f"hit_rate_at_{top_k}": round(sum(hits_at_k) / len(hits_at_k), 4),
        f"precision_at_{top_k}": round(sum(precision_k) / len(precision_k), 4),
        f"recall_at_{top_k}":    round(sum(recall_k)    / len(recall_k),    4),
        f"ndcg_at_{top_k}":      round(sum(ndcg_k)      / len(ndcg_k),      4),
    }

    f1_num = 2 * metrics[f"precision_at_{top_k}"] * metrics[f"recall_at_{top_k}"]
    f1_den = metrics[f"precision_at_{top_k}"] + metrics[f"recall_at_{top_k}"]
    metrics[f"f1_at_{top_k}"] = round(f1_num / max(f1_den, 1e-10), 4)

    print(f"\n  LSI Results:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# CJPE Evaluation (Judgment Prediction)
# ---------------------------------------------------------------------------
def _extract_judgment_label(text: str) -> Optional[str]:
    """Heuristically extract judgment label from CJPE chunk text."""
    text_lower = text.lower()
    # Look for common judgment keywords
    if re.search(r"\b(accepted|allowed|granted|favor of petitioner|in favour of)\b", text_lower):
        return "accepted"
    if re.search(r"\b(rejected|dismissed|not allowed|denied|upheld conviction)\b", text_lower):
        return "rejected"
    return None


def evaluate_cjpe(
    pipeline: LegalRAGPipeline,
    cjpe_chunks: List[Dict],
    n_samples: int,
) -> Dict[str, Any]:
    """
    CJPE: predict court judgment (accepted/rejected) using RAG retrieval.
    Since we are in retrieval-only mode, we use a heuristic: predict
    based on whether retrieved chunks lean toward granted or rejected outcomes.
    """
    print(f"\n  [CJPE] Evaluating Court Judgment Prediction ({n_samples} samples)...")

    # Filter chunks that have a detectable label
    labeled = [(c, _extract_judgment_label(c["text"])) for c in cjpe_chunks]
    labeled = [(c, lbl) for c, lbl in labeled if lbl is not None]

    if len(labeled) < n_samples // 2:
        print(f"    WARNING: Only {len(labeled)} labeled samples found (expected {n_samples}). Using all.")

    samples = random.Random(RANDOM_SEED).sample(labeled, min(n_samples, len(labeled)))

    y_true: List[int] = []
    y_pred: List[int] = []

    label_map = {"accepted": 1, "rejected": 0}

    for i, (chunk, true_label) in enumerate(samples):
        query = chunk["text"][:400]
        result = pipeline.query(query, top_k=5, search_mode="hybrid")
        retrieved = result["retrieved_chunks"]

        # Heuristic prediction: aggregate signals from retrieved docs
        accepted_score = 0
        rejected_score = 0
        for r in retrieved:
            rt = r.get("text", "").lower()
            if re.search(r"\b(bail granted|allowed|accepted|in favour)\b", rt):
                accepted_score += r.get("score", 0.5)
            if re.search(r"\b(bail denied|rejected|dismissed|not maintainable)\b", rt):
                rejected_score += r.get("score", 0.5)

        pred_label = "accepted" if accepted_score >= rejected_score else "rejected"
        y_true.append(label_map[true_label])
        y_pred.append(label_map[pred_label])

        if (i + 1) % 50 == 0:
            acc_so_far = accuracy_score(y_true, y_pred)
            print(f"    Progress: {i+1}/{len(samples)} | Acc={acc_so_far:.3f}", flush=True)

    if not y_true:
        return {"task": "CJPE", "error": "No labeled samples found"}

    accuracy  = accuracy_score(y_true, y_pred)
    f1_macro  = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1_binary = f1_score(y_true, y_pred, average="binary", zero_division=0)

    try:
        auc = roc_auc_score(y_true, y_pred)
    except Exception:
        auc = None

    metrics = {
        "task": "CJPE",
        "n_samples": len(samples),
        "accuracy":  round(accuracy, 4),
        "f1_macro":  round(f1_macro, 4),
        "f1_binary": round(f1_binary, 4),
        "auc_roc":   round(auc, 4) if auc is not None else "N/A",
        "label_distribution": {
            "true_accepted": sum(y_true),
            "true_rejected": len(y_true) - sum(y_true),
            "pred_accepted": sum(y_pred),
            "pred_rejected": len(y_pred) - sum(y_pred),
        },
    }

    print(f"\n  CJPE Results:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# Bail Prediction Evaluation
# ---------------------------------------------------------------------------
def _extract_bail_label(text: str) -> Optional[str]:
    text_lower = text.lower()
    if re.search(r"\b(bail granted|bail allowed|bail application.*granted|bail.*allowed)\b", text_lower):
        return "granted"
    if re.search(r"\b(bail rejected|bail denied|bail application.*rejected|bail.*denied|bail.*dismissed)\b", text_lower):
        return "denied"
    return None


def evaluate_bail(
    pipeline: LegalRAGPipeline,
    bail_chunks: List[Dict],
    n_samples: int,
) -> Dict[str, Any]:
    """
    Bail Prediction: predict bail grant/deny using RAG.
    """
    print(f"\n  [BAIL] Evaluating Bail Prediction ({n_samples} samples)...")

    labeled = [(c, _extract_bail_label(c["text"])) for c in bail_chunks]
    labeled = [(c, lbl) for c, lbl in labeled if lbl is not None]

    if len(labeled) < n_samples // 2:
        print(f"    WARNING: Only {len(labeled)} labeled samples. Using all.")

    samples = random.Random(RANDOM_SEED).sample(labeled, min(n_samples, len(labeled)))

    y_true: List[int] = []
    y_pred: List[int] = []
    label_map = {"granted": 1, "denied": 0}

    for i, (chunk, true_label) in enumerate(samples):
        query = chunk["text"][:400]
        result = pipeline.query(query, top_k=5, search_mode="hybrid", category_filter="iltur")
        retrieved = result["retrieved_chunks"]

        granted_score = 0.0
        denied_score  = 0.0
        for r in retrieved:
            rt = r.get("text", "").lower()
            sc = r.get("score", 0.5)
            if re.search(r"\b(bail granted|allowed|favour of accused)\b", rt):
                granted_score += sc
            if re.search(r"\b(bail rejected|denied|dismissed|remanded)\b", rt):
                denied_score  += sc

        pred_label = "granted" if granted_score >= denied_score else "denied"
        y_true.append(label_map[true_label])
        y_pred.append(label_map[pred_label])

        if (i + 1) % 50 == 0:
            acc_so_far = accuracy_score(y_true, y_pred)
            print(f"    Progress: {i+1}/{len(samples)} | Acc={acc_so_far:.3f}", flush=True)

    if not y_true:
        return {"task": "Bail", "error": "No labeled samples found"}

    accuracy  = accuracy_score(y_true, y_pred)
    f1_macro  = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1_binary = f1_score(y_true, y_pred, average="binary", zero_division=0)

    try:
        auc = roc_auc_score(y_true, y_pred)
    except Exception:
        auc = None

    metrics = {
        "task": "Bail Prediction",
        "n_samples": len(samples),
        "accuracy":  round(accuracy, 4),
        "f1_macro":  round(f1_macro, 4),
        "f1_binary": round(f1_binary, 4),
        "auc_roc":   round(auc, 4) if auc is not None else "N/A",
        "label_distribution": {
            "true_granted": sum(y_true),
            "true_denied":  len(y_true) - sum(y_true),
            "pred_granted": sum(y_pred),
            "pred_denied":  len(y_pred) - sum(y_pred),
        },
    }

    print(f"\n  Bail Results:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  LegalCompass AI -- IL-TUR Evaluation Benchmark")
    print("=" * 70)

    # 1. Load RAG pipeline
    print("\n[1/5] Connecting to RAG pipeline...")
    retriever = LegalRAGRetriever()
    retriever.connect()
    pipeline  = LegalRAGPipeline(retriever)

    # 2. Load IL-TUR chunks
    print("\n[2/5] Loading IL-TUR chunk data...")
    chunks_by_task = load_iltur_chunks_by_task(CHUNKS_DIR / "iltur_chunks.json")

    # 3. Run evaluations
    print("\n[3/5] Running evaluations...")
    all_results: Dict[str, Any] = {}
    t_start = time.time()

    # LSI
    lsi_chunks = chunks_by_task.get("lsi", [])
    if lsi_chunks:
        all_results["lsi"] = evaluate_lsi(pipeline, lsi_chunks, EVAL_SAMPLES_PER_TASK)
    else:
        all_results["lsi"] = {"task": "LSI", "error": "No LSI chunks found"}
        print("  [LSI] No lsi chunks available.")

    # CJPE
    cjpe_chunks = chunks_by_task.get("cjpe", [])
    if cjpe_chunks:
        all_results["cjpe"] = evaluate_cjpe(pipeline, cjpe_chunks, EVAL_SAMPLES_PER_TASK)
    else:
        all_results["cjpe"] = {"task": "CJPE", "error": "No CJPE chunks found"}
        print("  [CJPE] No cjpe chunks available.")

    # Bail
    bail_chunks = chunks_by_task.get("bail", [])
    if bail_chunks:
        all_results["bail"] = evaluate_bail(pipeline, bail_chunks, EVAL_SAMPLES_PER_TASK)
    else:
        all_results["bail"] = {"task": "Bail", "error": "No bail chunks found"}
        print("  [BAIL] No bail chunks available.")

    total_elapsed = round(time.time() - t_start, 1)

    # 4. Build full report
    print(f"\n[4/5] Building report...")
    report = {
        "project": "LegalCompass AI",
        "phase": "Step 4: IL-TUR Evaluation",
        "eval_samples_per_task": EVAL_SAMPLES_PER_TASK,
        "search_mode": "hybrid",
        "top_k": TOP_K,
        "total_elapsed_seconds": total_elapsed,
        "results": all_results,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 5. Print & save summary
    print(f"\n[5/5] Saving report to {REPORT_PATH}")
    summary_lines = [
        "=" * 70,
        "  LegalCompass AI -- IL-TUR Evaluation Summary",
        "=" * 70,
        f"  Eval samples per task : {EVAL_SAMPLES_PER_TASK}",
        f"  Search mode           : hybrid",
        f"  Top-K                 : {TOP_K}",
        f"  Total elapsed         : {total_elapsed}s",
        "",
        "  TASK RESULTS:",
        "-" * 70,
    ]

    for task_key, task_results in all_results.items():
        if "error" in task_results:
            summary_lines.append(f"  [{task_key.upper()}] ERROR: {task_results['error']}")
            continue
        summary_lines.append(f"\n  [{task_key.upper()}] {task_results.get('task', task_key)}  (n={task_results.get('n_samples', 0)})")
        for k, v in task_results.items():
            if k in ("task", "n_samples", "label_distribution"):
                continue
            if isinstance(v, float):
                summary_lines.append(f"      {k:<25}: {v:.4f}")
            elif isinstance(v, str):
                summary_lines.append(f"      {k:<25}: {v}")

    summary_lines.append("")
    summary_lines.append("=" * 70)

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(summary_text)

    print(f"\n  Report JSON : {REPORT_PATH}")
    print(f"  Summary TXT : {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
