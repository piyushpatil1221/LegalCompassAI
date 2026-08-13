"""LegalCompass AI — Fixed API Server"""
import json, os, sys, time, asyncio, hashlib, subprocess, textwrap
from collections import OrderedDict
from pathlib import Path
from urllib.parse import quote
from typing import Optional
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

REQUIRED = ["fastapi","uvicorn","sentence_transformers","chromadb"]
for pkg in REQUIRED:
    try: __import__(pkg.replace("-","_"))
    except ImportError:
        print(f"pip install {pkg}"); sys.exit(1)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - optional dependency
    canvas = None
    letter = None

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

ROOT_DIR = PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR.parent))

from LegalCompassAI.extract_text import extract_text
from LegalCompassAI.summarize import summarize_text

sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import LegalRAGRetriever, LegalRAGPipeline

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR  = PROJECT_DIR / "BNS DATASET" / "output"
WEBAPP_DIR  = PROJECT_DIR / "webapp"
REPORT_PATH = OUTPUT_DIR / "embeddings_report.json"
EVAL_REPORT = OUTPUT_DIR / "evaluation_report.json"
SUMMARY_TMP_DIR = PROJECT_DIR.parent / "tmp_summaries"

retriever = None
pipeline  = None
agent_orchestrator = None

# Simple LRU cache for repeated queries (avoids redundant embedding + ChromaDB round-trips)
class _LRUCache:
    def __init__(self, maxsize: int = 128):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
    def get(self, key: str):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    def set(self, key: str, value):
        self._cache[key] = value
        self._cache.move_to_end(key)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

_query_cache  = _LRUCache(128)
_search_cache = _LRUCache(128)
_session_store = {}

_live_metrics = {
    "total_queries": 0,
    "total_drafts": 0,
    "total_latency_ms": 0,
    "avg_confidence": 0,
    "crime_counts": {},
    "bail_counts": {"GRANTED": 0, "REJECTED": 0},
    "latency_history": []
}

def _cache_key(*args) -> str:
    return hashlib.md5("|".join(str(a) for a in args).encode()).hexdigest()

def _run_script(script_name: str):
    script_path = PROJECT_DIR / "scripts" / script_name
    if not script_path.exists():
        return False

    print(f"[Server] Running {script_name}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_DIR))
    return result.returncode == 0


def _has_indexed_data() -> bool:
    """Return True when at least one legal collection has been embedded."""
    if not (OUTPUT_DIR / "chroma_db").exists():
        return False
    report_path = OUTPUT_DIR / "embeddings_report.json"
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            total = data.get("total_chunks_indexed")
            if isinstance(total, int) and total > 0:
                return True
        except Exception:
            pass

    chunk_files = [
        OUTPUT_DIR / "chunks" / "bare_acts_chunks.json",
        OUTPUT_DIR / "chunks" / "case_docs_chunks.json",
        OUTPUT_DIR / "chunks" / "crime_stats_chunks.json",
        OUTPUT_DIR / "chunks" / "iltur_chunks.json",
    ]
    return any(p.exists() and p.stat().st_size > 0 for p in chunk_files)


def _indexed_count() -> int:
    try:
        report_path = OUTPUT_DIR / "embeddings_report.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            total = data.get("total_chunks_indexed")
            if isinstance(total, int):
                return total
    except Exception:
        pass

    total = 0
    for chunk_file in [
        OUTPUT_DIR / "chunks" / "bare_acts_chunks.json",
        OUTPUT_DIR / "chunks" / "case_docs_chunks.json",
        OUTPUT_DIR / "chunks" / "crime_stats_chunks.json",
        OUTPUT_DIR / "chunks" / "iltur_chunks.json",
    ]:
        if chunk_file.exists():
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    total += len(data)
                elif isinstance(data, dict):
                    total += int(data.get("count", 0) or 0)
            except Exception:
                pass
    return total


def _ensure_corpus_ready():
    """Auto-build the corpus when the legal app starts if any required indexed artifacts are missing."""
    if _has_indexed_data():
        return True

    print("[Server] Legal corpus not ready. Auto-initialising data pipeline...")

    if not (PROJECT_DIR / "BNS DATASET" / "output").exists():
        (PROJECT_DIR / "BNS DATASET" / "output").mkdir(parents=True, exist_ok=True)

    scripts_to_run = [
        "extract_bare_acts.py",
        "convert_case_docs.py",
        "convert_crime_csvs.py",
        "chunk_corpus.py",
        "embed_and_index.py",
        "build_corpus_index.py",
    ]

    for script in scripts_to_run:
        ok = _run_script(script)
        if not ok:
            print(f"[Server] WARNING: {script} did not complete successfully; continuing startup anyway.")

    return _has_indexed_data()


def _load_pipeline():
    """Blocking pipeline init — runs in thread pool to avoid blocking event loop."""
    global retriever, pipeline
    print("[Server] Loading RAG pipeline...")
    _ensure_corpus_ready()
    r = LegalRAGRetriever()
    try:
        r.connect()
        pipeline = LegalRAGPipeline(r)
        retriever = r
        
        import sys
        if str(PROJECT_DIR) not in sys.path:
            sys.path.insert(0, str(PROJECT_DIR))
        from orchestrator import LegalCompassOrchestrator
        global agent_orchestrator
        agent_orchestrator = LegalCompassOrchestrator(retriever=r)
        
        print("[Server] RAG pipeline and Agent Orchestrator ready.")
    except Exception as e:
        print(f"[Server] WARNING: RAG pipeline/Orchestrator failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        await loop.run_in_executor(pool, _load_pipeline)
    yield

app = FastAPI(title="LegalCompass AI", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    question: str
    top_k: int = 8
    search_mode: str = "hybrid"
    category_filter: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/api/query")
async def api_query(req: QueryRequest):
    if not pipeline:
        raise HTTPException(503, "RAG pipeline not ready. Run embed_and_index.py first.")
    key = _cache_key(req.question, req.top_k, req.search_mode, req.category_filter)
    cached = _query_cache.get(key)
    if cached is not None:
        return cached
    try:
        result = pipeline.query(req.question, req.top_k, req.search_mode, req.category_filter)
        _query_cache.set(key, result)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/agent-query")
async def api_agent_query(req: QueryRequest):
    if not agent_orchestrator:
        raise HTTPException(503, "Agent Orchestrator not ready.")
    
    import uuid
    session_id = req.session_id or str(uuid.uuid4())
    session_history = _session_store.get(session_id, [])
    
    # Detect document drafting request
    is_draft_requested = any(w in req.question.lower() for w in ["draft", "download", "downloadable", "template", "application"])

    key = _cache_key("agent", req.question, session_id)
    cached = _query_cache.get(key)
    if cached is not None:
        return cached
        
    try:
        t0 = time.time()
        # Run 5-agent pipeline (now 6-agent)
        case_rep = agent_orchestrator.run_pipeline(req.question, session_history=session_history, is_draft_requested=is_draft_requested)
        
        # Update history
        session_history.append({"role": "user", "content": req.question})
        session_history.append({"role": "assistant", "content": case_rep.get("guidance", {}).get("explanation", "")})
        _session_store[session_id] = session_history
        
        # Format chunks to match UI
        retrieved_chunks = []
        for s in case_rep.get("retrieved_statutes", []):
            retrieved_chunks.append({
                "text": s,
                "title": "BNS / Statutory Law",
                "category": "bare_acts",
                "score": 0.95
            })
        for p in case_rep.get("retrieved_precedents", []):
            retrieved_chunks.append({
                "text": p["facts_summary"],
                "title": p["case_name"],
                "category": "case_docs",
                "score": 0.90,
                "outcome": p.get("outcome", "Unknown")
            })
            
        # Update Live Metrics
        elapsed_ms = int((time.time() - t0) * 1000)
        _live_metrics["total_queries"] += 1
        _live_metrics["total_latency_ms"] += elapsed_ms
        _live_metrics["latency_history"].append(elapsed_ms)
        if len(_live_metrics["latency_history"]) > 50:
            _live_metrics["latency_history"].pop(0)
            
        if is_draft_requested and case_rep.get("drafted_document"):
            _live_metrics["total_drafts"] += 1
            
        # Update crime counts
        for c in case_rep.get("crime_types", []):
            cr = c.get("crime", "Unknown")
            _live_metrics["crime_counts"][cr] = _live_metrics["crime_counts"].get(cr, 0) + 1
            
        # Update bail counts
        bp = case_rep.get("guidance", {}).get("bail_prediction")
        if bp:
            bp = bp.upper()
            if bp in _live_metrics["bail_counts"]:
                _live_metrics["bail_counts"][bp] += 1
            else:
                _live_metrics["bail_counts"][bp] = 1
                
        # Confidence logic (Avg of role confidence if available)
        conf = case_rep.get("role_confidence", 0)
        if conf > 0:
            total_q = _live_metrics["total_queries"]
            _live_metrics["avg_confidence"] = (_live_metrics["avg_confidence"] * (total_q - 1) + conf) / total_q
            
        result = {
            "answer": case_rep.get("guidance", {}).get("explanation", ""),
            "retrieved_chunks": retrieved_chunks,
            "retrieved_count": len(retrieved_chunks),
            "elapsed_ms": elapsed_ms,
            "search_mode": "multi-agent",
            "agent_data": {
                "crime_types": case_rep.get("crime_types", []),
                "role": case_rep.get("role", ""),
                "clarification": case_rep.get("agent2_clarification"),
                "bail_prediction": case_rep.get("guidance", {}).get("bail_prediction"),
                "anonymized_summary": case_rep.get("anonymized_summary")
            },
            "drafted_document": case_rep.get("drafted_document"),
            "session_id": session_id
        }
        _query_cache.set(key, result)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))

@app.get("/api/search")
async def api_search(
    q: str = Query(...), top_k: int = 8,
    category: Optional[str] = None, mode: str = "hybrid"
):
    if not retriever:
        raise HTTPException(503, "Retriever not ready.")
    key = _cache_key(q, top_k, category, mode)
    cached = _search_cache.get(key)
    if cached is not None:
        return cached
    try:
        if mode == "hybrid":
            results = retriever.hybrid_search(q, top_k=top_k, category_filter=category)
        else:
            results = retriever.semantic_search(q, top_k=top_k, category_filter=category)
        result = {"query": q, "results": [r.to_dict() for r in results]}
        _search_cache.set(key, result)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/section/{act}/{section_number}")
async def api_section(act: str, section_number: str):
    if not retriever:
        raise HTTPException(503, "Retriever not ready.")
    result = retriever.section_lookup(act, section_number)
    if not result:
        raise HTTPException(404, f"{act} Section {section_number} not found.")
    return result.to_dict()

@app.get("/api/stats")
async def api_stats():
    data: dict = {}
    for path, key in [(OUTPUT_DIR/"chunks"/"chunks_summary.json","chunks"),
                      (REPORT_PATH,"embeddings"), (EVAL_REPORT,"evaluation"),
                      (OUTPUT_DIR/"corpus_index.json","corpus")]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data[key] = json.load(f)
    return data

@app.get("/api/collections")
async def api_collections():
    if not retriever or not retriever._client:
        return {"collections": []}
    return {"collections": [{"name": c.name, "count": c.count()}
                             for c in retriever._client.list_collections()]}

@app.get("/api/evaluation")
async def api_evaluation():
    if EVAL_REPORT.exists():
        with open(EVAL_REPORT, encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Run evaluate_iltur.py first."}

@app.get("/api/live-analytics")
async def api_live_analytics():
    # Return a copy of the live metrics to prevent modification
    return {
        "metrics": _live_metrics,
        "avg_latency": int(_live_metrics["total_latency_ms"] / max(1, _live_metrics["total_queries"])),
        "avg_confidence_pct": int(_live_metrics["avg_confidence"] * 100)
    }

def _build_summary_pdf(summary_text: str, original_filename: str) -> Path:
    if canvas is None or letter is None:
        raise RuntimeError("reportlab is not installed. Install it to enable PDF exports.")

    SUMMARY_TMP_DIR.mkdir(exist_ok=True)
    stem = Path(original_filename).stem
    output_path = SUMMARY_TMP_DIR / f"{stem}_summary.pdf"

    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    pdf.setTitle(f"{stem} summary")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 760, "LegalCompass AI Summary")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 742, f"Source: {original_filename}")
    pdf.setFont("Helvetica", 11)
    y = 720
    for paragraph in summary_text.replace("\r", "").split("\n"):
        for line in textwrap.wrap(paragraph, width=95):
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = 760
            pdf.drawString(50, y, line)
            y -= 18
    pdf.save()
    return output_path


@app.post("/api/summarize")
async def api_summarize(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file uploaded.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(400, "Only PDF and DOCX files are supported.")

    temp_dir = PROJECT_DIR.parent / "tmp_summaries"
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename

    try:
        contents = await file.read()
        temp_path.write_bytes(contents)
        text = extract_text(str(temp_path))
        summary = summarize_text(text)
        pdf_path = _build_summary_pdf(summary, file.filename)
        return {
            "filename": file.filename,
            "summary": summary,
            "status": "ok",
            "pdf_url": f"/api/download-summary/{quote(file.filename)}",
            "pdf_name": pdf_path.name,
        }
    except Exception as exc:
        raise HTTPException(500, f"Summarization failed: {exc}")
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/download-summary/{filename}")
async def download_summary(filename: str):
    raw_name = Path(filename).stem
    pdf_path = SUMMARY_TMP_DIR / f"{raw_name}_summary.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "Summary PDF not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{raw_name}_summary.pdf")


@app.get("/api/health")
async def health():
    has_indexed = _has_indexed_data()
    return {
        "status": "ok",
        "pipeline_ready": pipeline is not None and has_indexed,
        "retriever_ready": retriever is not None and retriever._client is not None and has_indexed,
        "indexed_chunks": _indexed_count(),
        "timestamp": time.time(),
    }

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    idx = WEBAPP_DIR / "index.html"
    if idx.exists():
        return HTMLResponse(content=idx.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Run from project root. webapp/index.html not found.</h1>")

if __name__ == "__main__":
    print("="*60)
    print("  LegalCompass AI  |  http://localhost:8000")
    print("="*60)
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
