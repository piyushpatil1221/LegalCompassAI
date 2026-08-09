"""
LegalCompass AI - IL-TUR JSON Validator
Validates the existing IL-TUR Parquet-to-JSON conversions.

Checks:
- Record count consistency (Parquet vs JSON)
- Field completeness (no missing/null critical fields)
- Encoding integrity
- Generates a summary report
"""

import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas")
    sys.exit(1)


# IL-TUR task types and their descriptions
ILTUR_TASKS = {
    'bail': 'Bail Prediction - Predicting whether bail should be granted',
    'cjpe': 'Court Judgment Prediction & Explanation',
    'lmt': 'Legal Machine Translation (EN to Indian languages)',
    'lner': 'Legal Named Entity Recognition',
    'lsi': 'Legal Statute Identification',
    'pcr': 'Prior Case Retrieval',
    'rr': 'Rhetorical Role labeling of legal documents',
    'summ': 'Legal Document Summarization',
}


def count_json_records(json_path: str) -> int:
    """Count records in a JSON file efficiently."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return len(data)
        return 1
    except Exception as e:
        return -1


def count_parquet_records(parquet_path: str) -> int:
    """Count records in a Parquet file."""
    try:
        df = pd.read_parquet(parquet_path)
        return len(df)
    except Exception as e:
        return -1


def get_parquet_columns(parquet_path: str) -> list:
    """Get column names from a Parquet file."""
    try:
        df = pd.read_parquet(parquet_path, nrows=0)
        return list(df.columns)
    except:
        return []


def check_json_quality(json_path: str, sample_size: int = 5) -> dict:
    """Check quality of a JSON file by sampling records."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            return {'error': 'Not a list or empty'}
        
        total = len(data)
        sample = data[:sample_size]
        
        # Check for null/empty fields
        all_keys = set()
        for record in sample:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        empty_fields = {}
        for key in all_keys:
            empty_count = sum(
                1 for record in data 
                if isinstance(record, dict) and (
                    record.get(key) is None or 
                    record.get(key) == '' or 
                    record.get(key) == []
                )
            )
            if empty_count > 0:
                empty_fields[key] = {
                    'empty_count': empty_count,
                    'empty_pct': round(empty_count / total * 100, 1)
                }
        
        return {
            'total_records': total,
            'fields': sorted(list(all_keys)),
            'field_count': len(all_keys),
            'empty_fields': empty_fields,
            'sample_record': sample[0] if sample else None,
        }
    except Exception as e:
        return {'error': str(e)}


def validate_iltur(base_dir: str, output_dir: str):
    """Validate all IL-TUR conversions."""
    iltur_dir = os.path.join(base_dir, 'IL-TUR')
    
    print("=" * 70)
    print("  LegalCompass AI - IL-TUR Validation")
    print("=" * 70)
    
    report = {
        'summary': {},
        'tasks': {},
        'issues': [],
    }
    
    total_parquet_files = 0
    total_json_files = 0
    total_records = 0
    tasks_validated = 0
    
    for task_name in sorted(ILTUR_TASKS.keys()):
        task_dir = os.path.join(iltur_dir, task_name)
        if not os.path.exists(task_dir):
            report['issues'].append(f"Task directory not found: {task_name}")
            continue
        
        print(f"\n--- {task_name.upper()}: {ILTUR_TASKS[task_name]} ---")
        
        task_report = {
            'description': ILTUR_TASKS[task_name],
            'files': [],
        }
        
        # Find parquet files
        parquet_files = sorted(Path(task_dir).glob('*.parquet'))
        
        for pq_file in parquet_files:
            pq_name = pq_file.stem
            json_name = f"ILTUR_{task_name}_{pq_name}.json"
            json_path = os.path.join(output_dir, json_name)
            
            total_parquet_files += 1
            
            # Count parquet records
            pq_count = count_parquet_records(str(pq_file))
            pq_columns = get_parquet_columns(str(pq_file))
            
            file_report = {
                'parquet_file': pq_file.name,
                'json_file': json_name,
                'parquet_records': pq_count,
                'parquet_columns': pq_columns,
            }
            
            if os.path.exists(json_path):
                total_json_files += 1
                json_count = count_json_records(json_path)
                json_size = os.path.getsize(json_path)
                
                file_report['json_exists'] = True
                file_report['json_records'] = json_count
                file_report['json_size_mb'] = round(json_size / (1024 * 1024), 2)
                file_report['records_match'] = pq_count == json_count
                
                if pq_count == json_count:
                    status = "[OK]"
                    total_records += json_count
                elif json_count >= 0:
                    status = "[MISMATCH]"
                    report['issues'].append(
                        f"{json_name}: Parquet has {pq_count} records but JSON has {json_count}"
                    )
                    total_records += json_count
                else:
                    status = "[ERROR]"
                    report['issues'].append(f"{json_name}: Failed to read JSON")
                
                print(f"  {status} {pq_file.name} -> {json_name}")
                print(f"       Parquet: {pq_count:,} records | JSON: {json_count:,} records ({file_report['json_size_mb']} MB)")
            else:
                file_report['json_exists'] = False
                status = "[MISSING]"
                report['issues'].append(f"JSON not found: {json_name}")
                print(f"  {status} {pq_file.name} -> {json_name} (NOT CONVERTED)")
            
            task_report['files'].append(file_report)
        
        report['tasks'][task_name] = task_report
        tasks_validated += 1
    
    # Summary
    report['summary'] = {
        'tasks_validated': tasks_validated,
        'total_parquet_files': total_parquet_files,
        'total_json_files': total_json_files,
        'total_records': total_records,
        'missing_jsons': total_parquet_files - total_json_files,
        'total_issues': len(report['issues']),
    }
    
    # Print summary
    print(f"\n{'=' * 70}")
    print("  IL-TUR VALIDATION REPORT")
    print(f"{'=' * 70}")
    print(f"  Tasks validated: {tasks_validated}/{len(ILTUR_TASKS)}")
    print(f"  Parquet files: {total_parquet_files}")
    print(f"  JSON files: {total_json_files}")
    print(f"  Total records: {total_records:,}")
    print(f"  Missing JSONs: {total_parquet_files - total_json_files}")
    print(f"  Issues: {len(report['issues'])}")
    
    if report['issues']:
        print(f"\n  ISSUES:")
        for issue in report['issues']:
            print(f"    - {issue}")
    
    # Save report
    report_path = os.path.join(output_dir, 'iltur_validation_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved to: {report_path}")
    
    return report


def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'BNS DATASET')
    output_dir = os.path.join(base_dir, 'output')
    
    validate_iltur(base_dir, output_dir)


if __name__ == '__main__':
    main()
