"""
LegalCompass AI - Step 1: Chunking & Preprocessing Engine
Applies domain-aware chunking strategies across all legal corpus datasets.

Output:
- BNS DATASET/output/chunks/bare_acts_chunks.json
- BNS DATASET/output/chunks/case_docs_chunks.json
- BNS DATASET/output/chunks/iltur_chunks.json
- BNS DATASET/output/chunks/crime_stats_chunks.json
- BNS DATASET/output/chunks/chunks_summary.json
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any


def recursive_character_split(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks using recursive character delimiters."""
    if not text or len(text.strip()) == 0:
        return []
    
    if len(text) <= chunk_size:
        return [text.strip()]
    
    separators = ["\n\n", "\n", ". ", "; ", ", ", " "]
    chunks = []
    
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:].strip())
            break
        
        # Try finding a good separator near the end
        best_end = end
        for sep in separators:
            pos = text.rfind(sep, start + chunk_size // 2, end)
            if pos != -1:
                best_end = pos + len(sep)
                break
        
        chunk = text[start:best_end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = best_end - chunk_overlap
        if start < 0 or start >= text_len:
            break
            
    return [c for c in chunks if len(c) > 20]


def chunk_bare_acts(output_dir: str) -> List[Dict[str, Any]]:
    """
    Chunk Bare Acts using Section-Bound strategy (1 section = 1 chunk).
    Preserves all section metadata, sub-sections, explanations, and illustrations.
    """
    print("  [1/4] Chunking Bare Acts (BNS, BNSS, BSA)...")
    chunks = []
    
    act_files = ['BNS_structured.json', 'BNSS_structured.json', 'BSA_structured.json']
    
    for filename in act_files:
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            print(f"        [WARN] File not found: {filename}")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        sections = data.get('sections', [])
        act_short = data.get('metadata', {}).get('act_short', filename.split('_')[0])
        act_full = data.get('metadata', {}).get('act', '')
        
        for sec in sections:
            sec_num = sec.get('section_number', '')
            sec_title = sec.get('section_title', '')
            ch_num = sec.get('chapter_number', '')
            ch_title = sec.get('chapter_title', '')
            sec_text = sec.get('text', '').strip()
            
            if not sec_text:
                continue
                
            chunk_id = f"{act_short}_S{str(sec_num).zfill(3)}_C01"
            title = f"{act_short} Section {sec_num}: {sec_title}" if sec_title else f"{act_short} Section {sec_num}"
            
            chunk = {
                "chunk_id": chunk_id,
                "corpus_category": "bare_act",
                "source_file": filename,
                "title": title,
                "text": sec_text,
                "char_length": len(sec_text),
                "metadata": {
                    "act_full": act_full,
                    "act_short": act_short,
                    "chapter_number": ch_num,
                    "chapter_title": ch_title,
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "cross_references": sec.get('cross_references', []),
                    "has_illustrations": sec.get('has_illustrations', False),
                    "has_explanations": sec.get('has_explanations', False),
                    "illustration_count": sec.get('illustration_count', 0),
                    "explanation_count": sec.get('explanation_count', 0)
                }
            }
            chunks.append(chunk)
            
    print(f"        -> Generated {len(chunks):,} section chunks from Bare Acts.")
    return chunks


def chunk_case_docs(output_dir: str) -> List[Dict[str, Any]]:
    """
    Chunk Case Documents using Recursive Character Splitting.
    """
    print("  [2/4] Chunking Case Documents (IPC 302 / BNS 103)...")
    chunks = []
    case_dir = os.path.join(output_dir, 'case_docs')
    
    if not os.path.exists(case_dir):
        print("        [WARN] Case docs directory not found.")
        return chunks
        
    for filename in sorted(os.listdir(case_dir)):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(case_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        records = data.get('records', [])
        
        for idx, rec in enumerate(records):
            # Combine record fields into a full text block
            text_parts = []
            for k, v in rec.items():
                if k.startswith('_'):
                    continue
                if v and str(v).strip():
                    text_parts.append(f"{k}: {str(v).strip()}")
                    
            full_text = "\n".join(text_parts)
            if not full_text.strip():
                continue
                
            text_splits = recursive_character_split(full_text, chunk_size=1000, chunk_overlap=200)
            
            for part_idx, split_text in enumerate(text_splits):
                chunk_id = f"CASE_{Path(filename).stem}_R{str(idx+1).zfill(5)}_P{str(part_idx+1).zfill(2)}"
                case_title = rec.get('title') or rec.get('case_name') or rec.get('Case Name') or f"Record {idx+1}"
                
                chunk = {
                    "chunk_id": chunk_id,
                    "corpus_category": "case_docs",
                    "source_file": filename,
                    "title": f"Case Doc: {case_title} (Part {part_idx+1})",
                    "text": split_text,
                    "char_length": len(split_text),
                    "metadata": {
                        "record_index": idx + 1,
                        "part_index": part_idx + 1,
                        "total_parts": len(text_splits),
                        "sheet": rec.get('_sheet', ''),
                        "case_name": case_title
                    }
                }
                chunks.append(chunk)
                
    print(f"        -> Generated {len(chunks):,} chunks from Case Documents.")
    return chunks


def chunk_iltur_datasets(output_dir: str) -> List[Dict[str, Any]]:
    """
    Chunk IL-TUR Benchmark datasets.
    Focuses on RAG-relevant subsets: lsi, pcr, summ, bail, cjpe, lmt, lner, rr.
    """
    print("  [3/4] Chunking IL-TUR Benchmark Datasets...")
    chunks = []
    
    iltur_files = [f for f in sorted(os.listdir(output_dir)) if f.startswith('ILTUR_') and f.endswith('.json')]
    
    for filename in iltur_files:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            continue
            
        # Infer task type from filename (e.g., ILTUR_bail_..., ILTUR_summ_...)
        parts = filename.split('_')
        task_type = parts[1] if len(parts) > 1 else "iltur"
        
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                continue
                
            # Extract text field based on common IL-TUR fields
            text = (item.get('text') or item.get('summary') or item.get('query') or 
                    item.get('fact') or item.get('document') or str(item))
            
            if not isinstance(text, str) or len(text.strip()) == 0:
                continue
                
            text_splits = recursive_character_split(text.strip(), chunk_size=1200, chunk_overlap=200)
            
            for part_idx, split_text in enumerate(text_splits):
                chunk_id = f"ILTUR_{task_type.upper()}_{Path(filename).stem}_R{str(idx+1).zfill(6)}_P{str(part_idx+1).zfill(2)}"
                
                chunk = {
                    "chunk_id": chunk_id,
                    "corpus_category": "iltur",
                    "source_file": filename,
                    "title": f"IL-TUR [{task_type.upper()}] Record {idx+1} (Part {part_idx+1})",
                    "text": split_text,
                    "char_length": len(split_text),
                    "metadata": {
                        "task_type": task_type,
                        "record_index": idx + 1,
                        "part_index": part_idx + 1,
                        "id": item.get('id', '')
                    }
                }
                chunks.append(chunk)
                
    print(f"        -> Generated {len(chunks):,} chunks from IL-TUR Datasets.")
    return chunks


def chunk_crime_stats(output_dir: str) -> List[Dict[str, Any]]:
    """
    Chunk Crime Statistics datasets using row-group statistical text aggregation.
    """
    print("  [4/4] Chunking Crime Statistics CSV Datasets...")
    chunks = []
    stats_dir = os.path.join(output_dir, 'crime_stats')
    
    if not os.path.exists(stats_dir):
        print("        [WARN] Crime stats directory not found.")
        return chunks
        
    for filename in sorted(os.listdir(stats_dir)):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(stats_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        dataset_name = data.get('dataset', Path(filename).stem)
        records = data.get('records', [])
        
        # Group records into blocks of 10 for aggregated summary text
        group_size = 10
        for i in range(0, len(records), group_size):
            group = records[i:i+group_size]
            
            lines = [f"Dataset: {dataset_name}"]
            for r in group:
                fields = [f"{k}: {v}" for k, v in r.items() if v is not None and str(v).strip()]
                lines.append(" | ".join(fields[:8]))  # Top key fields
                
            agg_text = "\n".join(lines)
            chunk_id = f"STAT_{Path(filename).stem}_G{str(i//group_size+1).zfill(4)}"
            
            chunk = {
                "chunk_id": chunk_id,
                "corpus_category": "crime_stats",
                "source_file": filename,
                "title": f"Crime Stats: {dataset_name} (Group {i//group_size+1})",
                "text": agg_text,
                "char_length": len(agg_text),
                "metadata": {
                    "dataset_name": dataset_name,
                    "group_index": i // group_size + 1,
                    "record_range": f"{i+1}-{min(i+group_size, len(records))}",
                    "total_records_in_dataset": len(records)
                }
            }
            chunks.append(chunk)
            
    print(f"        -> Generated {len(chunks):,} chunks from Crime Statistics.")
    return chunks


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_dir, 'BNS DATASET', 'output')
    chunks_dir = os.path.join(output_dir, 'chunks')
    os.makedirs(chunks_dir, exist_ok=True)
    
    print("=" * 70)
    print("  LegalCompass AI - Step 1: Corpus Chunking & Preprocessing Engine")
    print("=" * 70)
    
    # 1. Bare Acts
    bare_acts_chunks = chunk_bare_acts(output_dir)
    with open(os.path.join(chunks_dir, 'bare_acts_chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(bare_acts_chunks, f, indent=2, ensure_ascii=False)
        
    # 2. Case Docs
    case_docs_chunks = chunk_case_docs(output_dir)
    with open(os.path.join(chunks_dir, 'case_docs_chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(case_docs_chunks, f, indent=2, ensure_ascii=False)
        
    # 3. Crime Stats
    crime_stats_chunks = chunk_crime_stats(output_dir)
    with open(os.path.join(chunks_dir, 'crime_stats_chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(crime_stats_chunks, f, indent=2, ensure_ascii=False)
        
    # 4. IL-TUR Datasets
    iltur_chunks = chunk_iltur_datasets(output_dir)
    with open(os.path.join(chunks_dir, 'iltur_chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(iltur_chunks, f, indent=2, ensure_ascii=False)
        
    # Generate Summary Report
    all_chunks_count = (len(bare_acts_chunks) + len(case_docs_chunks) + 
                        len(crime_stats_chunks) + len(iltur_chunks))
                        
    summary = {
        "project": "LegalCompass AI",
        "phase": "Step 1: Chunking & Preprocessing",
        "total_chunks_generated": all_chunks_count,
        "categories": {
            "bare_acts": {
                "chunk_count": len(bare_acts_chunks),
                "strategy": "Section-Bound (1 Section = 1 Chunk)",
                "file": "bare_acts_chunks.json"
            },
            "case_docs": {
                "chunk_count": len(case_docs_chunks),
                "strategy": "Recursive Character Splitting (1000 chars, 200 overlap)",
                "file": "case_docs_chunks.json"
            },
            "crime_stats": {
                "chunk_count": len(crime_stats_chunks),
                "strategy": "Row-Group Aggregation",
                "file": "crime_stats_chunks.json"
            },
            "iltur": {
                "chunk_count": len(iltur_chunks),
                "strategy": "Task-Adapted Character Splitting (1200 chars)",
                "file": "iltur_chunks.json"
            }
        }
    }
    
    summary_path = os.path.join(chunks_dir, 'chunks_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\n{'=' * 70}")
    print("  CHUNKING SUMMARY REPORT")
    print(f"{'=' * 70}")
    print(f"  Bare Acts Chunks  : {len(bare_acts_chunks):,}")
    print(f"  Case Docs Chunks  : {len(case_docs_chunks):,}")
    print(f"  Crime Stats Chunks: {len(crime_stats_chunks):,}")
    print(f"  IL-TUR Chunks     : {len(iltur_chunks):,}")
    print(f"  -------------------------------------")
    print(f"  TOTAL CHUNKS      : {all_chunks_count:,}")
    print(f"  Chunks Directory  : {chunks_dir}")
    print()


if __name__ == '__main__':
    main()
