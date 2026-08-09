"""
LegalCompass AI - Crime Statistics CSV to JSON Converter
Converts NCRB crime statistics CSV files to structured JSON.
"""

import json
import os
import sys
import re
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas")
    sys.exit(1)


def parse_csv_filename(filename: str) -> dict:
    """Extract metadata from CSV filename."""
    name = Path(filename).stem
    
    # Try to extract year range
    year_match = re.search(r'(\d{4})(?:_(\d{4}))?', name)
    year_start = year_match.group(1) if year_match else None
    year_end = year_match.group(2) if year_match else year_start
    
    # Clean up the name for a readable title
    title = re.sub(r'^\d+_\d*_?', '', name)  # Remove leading number prefix
    title = re.sub(r'_\d{4}(?:_\d{4})?$', '', title)  # Remove trailing years
    title = title.replace('_', ' ').strip()
    
    return {
        'filename': filename,
        'title': title,
        'year_start': year_start,
        'year_end': year_end,
    }


def convert_csv_to_json(csv_path: str) -> dict:
    """Convert a single CSV file to structured JSON."""
    filename = os.path.basename(csv_path)
    metadata = parse_csv_filename(filename)
    
    try:
        # Read CSV with pandas
        df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='latin-1', on_bad_lines='skip')
        except Exception as e:
            return {'error': str(e), 'filename': filename}
    except Exception as e:
        return {'error': str(e), 'filename': filename}
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    # Convert to records
    records = df.to_dict(orient='records')
    
    # Clean NaN values
    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
    
    result = {
        'source': 'NCRB Crime Statistics',
        'dataset': metadata['title'],
        'filename': metadata['filename'],
        'year_range': {
            'start': metadata['year_start'],
            'end': metadata['year_end'],
        },
        'columns': list(df.columns),
        'total_records': len(records),
        'records': records,
    }
    
    return result


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(project_dir, 'DATASETS')
    crime_subdir = os.path.join(datasets_dir, 'crime')
    output_dir = os.path.join(project_dir, 'BNS DATASET', 'output', 'crime_stats')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("  LegalCompass AI - Crime Statistics CSV to JSON")
    print("=" * 70)
    
    # Collect all CSV files from both directories
    csv_files = []
    
    # Root level CSVs
    for f in sorted(Path(datasets_dir).glob('*.csv')):
        csv_files.append(str(f))
    
    # Crime subdirectory CSVs
    if os.path.exists(crime_subdir):
        for f in sorted(Path(crime_subdir).glob('*.csv')):
            csv_files.append(str(f))
    
    print(f"\n  Found {len(csv_files)} CSV files to convert")
    
    success = 0
    errors = 0
    total_records = 0
    
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        print(f"  Converting: {filename}...", end=' ')
        
        result = convert_csv_to_json(csv_path)
        
        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            errors += 1
            continue
        
        # Write JSON output
        json_name = Path(filename).stem + '.json'
        output_path = os.path.join(output_dir, json_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        total_records += result['total_records']
        success += 1
        print(f"[OK] {result['total_records']:,} records")
    
    print(f"\n{'=' * 70}")
    print(f"  CONVERSION REPORT")
    print(f"{'=' * 70}")
    print(f"  Files converted: {success}/{len(csv_files)}")
    print(f"  Errors: {errors}")
    print(f"  Total records: {total_records:,}")
    print(f"  Output: {output_dir}")
    print()


if __name__ == '__main__':
    main()
