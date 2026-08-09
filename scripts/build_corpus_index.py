"""
LegalCompass AI - Unified Corpus Index Generator
Creates a master index of all data sources for the RAG system.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


def get_json_stats(json_path: str) -> dict:
    """Get basic stats for a JSON file."""
    try:
        size = os.path.getsize(json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            if 'sections' in data:
                count = len(data['sections'])
                data_type = 'bare_act'
            elif 'records' in data:
                count = len(data['records'])
                data_type = 'dataset'
            else:
                count = 1
                data_type = 'document'
        elif isinstance(data, list):
            count = len(data)
            data_type = 'list'
        else:
            count = 1
            data_type = 'other'
        
        return {
            'records': count,
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2),
            'type': data_type,
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_dir, 'BNS DATASET', 'output')
    
    print("=" * 60)
    print("  LegalCompass AI - Corpus Index Generator")
    print("=" * 60)
    
    corpus_index = {
        'project': 'LegalCompass AI',
        'description': 'Unified legal corpus for RAG-based Indian Criminal Law assistant',
        'generated_at': datetime.now().isoformat(),
        'sources': {},
        'summary': {},
    }
    
    # ── 1. Bare Acts ────────────────────────────────────────
    print("\n  [1/4] Indexing Bare Acts...")
    bare_acts = {}
    for act_file in ['BNS_structured.json', 'BNSS_structured.json', 'BSA_structured.json']:
        path = os.path.join(output_dir, act_file)
        if os.path.exists(path):
            stats = get_json_stats(path)
            bare_acts[act_file] = {
                'path': act_file,
                'category': 'bare_act',
                **stats,
            }
            print(f"     [OK] {act_file}: {stats.get('records', '?')} sections ({stats.get('size_mb', '?')} MB)")
        else:
            print(f"     [MISSING] {act_file}")
    
    corpus_index['sources']['bare_acts'] = {
        'description': 'Official Bare Acts - BNS, BNSS, BSA (2023)',
        'files': bare_acts,
    }
    
    # ── 2. IL-TUR Dataset ──────────────────────────────────
    print("\n  [2/4] Indexing IL-TUR datasets...")
    iltur_files = {}
    iltur_total_records = 0
    iltur_total_size = 0
    
    for f in sorted(Path(output_dir).glob('ILTUR_*.json')):
        stats = get_json_stats(str(f))
        iltur_files[f.name] = {
            'path': f.name,
            'category': 'iltur',
            **stats,
        }
        if 'records' in stats:
            iltur_total_records += stats['records']
            iltur_total_size += stats.get('size_bytes', 0)
    
    print(f"     Found {len(iltur_files)} IL-TUR files ({iltur_total_records:,} total records, {iltur_total_size/(1024*1024):.0f} MB)")
    
    corpus_index['sources']['iltur'] = {
        'description': 'IL-TUR Legal NLP Benchmark Dataset',
        'total_files': len(iltur_files),
        'total_records': iltur_total_records,
        'total_size_mb': round(iltur_total_size / (1024 * 1024), 2),
        'tasks': {
            'bail': 'Bail Prediction',
            'cjpe': 'Court Judgment Prediction & Explanation',
            'lmt': 'Legal Machine Translation',
            'lner': 'Legal Named Entity Recognition',
            'lsi': 'Legal Statute Identification',
            'pcr': 'Prior Case Retrieval',
            'rr': 'Rhetorical Role Labeling',
            'summ': 'Legal Document Summarization',
        },
        'files': {k: v for k, v in list(iltur_files.items())[:5]},  # Sample only
        'note': f'Full list contains {len(iltur_files)} files. Showing first 5 only.',
    }
    
    # ── 3. Crime Statistics ─────────────────────────────────
    print("\n  [3/4] Indexing Crime Statistics...")
    crime_dir = os.path.join(output_dir, 'crime_stats')
    crime_files = {}
    crime_total = 0
    
    if os.path.exists(crime_dir):
        for f in sorted(Path(crime_dir).glob('*.json')):
            stats = get_json_stats(str(f))
            crime_files[f.name] = stats
            crime_total += stats.get('records', 0)
        print(f"     Found {len(crime_files)} crime stat files ({crime_total:,} total records)")
    else:
        print(f"     [MISSING] Crime stats directory not yet created")
    
    corpus_index['sources']['crime_statistics'] = {
        'description': 'NCRB Crime Statistics (District-wise, by category)',
        'total_files': len(crime_files),
        'total_records': crime_total,
    }
    
    # ── 4. Case Documents ──────────────────────────────────
    print("\n  [4/4] Indexing Case Documents...")
    case_dir = os.path.join(output_dir, 'case_docs')
    case_files = {}
    case_total = 0
    
    if os.path.exists(case_dir):
        for f in sorted(Path(case_dir).glob('*.json')):
            stats = get_json_stats(str(f))
            case_files[f.name] = stats
            case_total += stats.get('records', 0)
        print(f"     Found {len(case_files)} case doc files ({case_total:,} total records)")
    else:
        print(f"     [MISSING] Case docs directory not yet created")
    
    corpus_index['sources']['case_documents'] = {
        'description': 'IPC 302 / BNS 103 Case Documents',
        'total_files': len(case_files),
        'total_records': case_total,
    }
    
    # ── Summary ────────────────────────────────────────────
    total_files = len(bare_acts) + len(iltur_files) + len(crime_files) + len(case_files)
    total_records = sum(s.get('records', 0) for s in bare_acts.values()) + iltur_total_records + crime_total + case_total
    
    corpus_index['summary'] = {
        'total_source_categories': 4,
        'total_json_files': total_files,
        'total_records': total_records,
        'rag_ready': True,
        'notes': [
            'Bare Acts: Structured by section with chapter/title metadata',
            'IL-TUR: Multi-task legal NLP benchmark data',
            'Crime Stats: NCRB district-level crime statistics',
            'Case Docs: IPC 302 murder case documents',
        ]
    }
    
    # Write index
    index_path = os.path.join(output_dir, 'corpus_index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(corpus_index, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print("  CORPUS INDEX SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total categories: 4")
    print(f"  Total JSON files: {total_files}")
    print(f"  Total records: {total_records:,}")
    print(f"  Index saved to: {index_path}")
    print()


if __name__ == '__main__':
    main()
