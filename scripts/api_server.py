"""LegalCompass AI — Fixed API Server"""
import json, os, sys, time, asyncio, hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

REQUIRED = ["fastapi","uvicorn","sentence_transformers","chromadb"]
for pkg in REQUIRED:
    try: __import__(pkg.replace("-","_"))
    except ImportError:
        print(f"pip install {pkg}"); sys.exit(1)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import LegalRAGRetriever, LegalRAGPipeline

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR  = PROJECT_DIR / "BNS DATASET" / "output"
WEBAPP_DIR  = PROJECT_DIR / "webapp"
REPORT_PATH = OUTPUT_DIR / "embeddings_report.json"
EVAL_REPORT = OUTPUT_DIR / "evaluation_report.json"

retriever = None
pipeline  = None

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

def _cache_key(*args) -> str:
    return hashlib.md5("|".join(str(a) for a in args).encode()).hexdigest()

def _load_pipeline():
    """Blocking pipeline init — runs in thread pool to avoid blocking event loop."""
    global retriever, pipeline
    print("[Server] Loading RAG pipeline...")
    r = LegalRAGRetriever()
    try:
        r.connect()
        pipeline = LegalRAGPipeline(r)
        retriever = r
        print("[Server] RAG pipeline ready.")
    except Exception as e:
        print(f"[Server] WARNING: RAG pipeline failed: {e}")

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

@app.get("/api/health")
async def health():
    return {"status":"ok","pipeline_ready": pipeline is not None,
            "retriever_ready": retriever is not None and retriever._client is not None,
            "timestamp": time.time()}

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
