"""
LegalCompass AI - IPC 302 Case Documents Converter
Converts Excel files containing IPC 302 (murder) case documents to JSON.
"""

import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas openpyxl")
    sys.exit(1)


def convert_excel_to_json(excel_path: str, output_dir: str) -> dict:
    """Convert an Excel file to structured JSON."""
    filename = os.path.basename(excel_path)
    print(f"  Reading: {filename}")
    
    try:
        # Read all sheets
        xls = pd.ExcelFile(excel_path, engine='openpyxl')
        sheets = xls.sheet_names
        print(f"     Sheets: {sheets}")
        
        all_records = []
        total = 0
        
        for sheet in sheets:
            df = pd.read_excel(excel_path, sheet_name=sheet, engine='openpyxl')
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Convert to records
            records = df.to_dict(orient='records')
            
            # Clean NaN values
            for record in records:
                for key, value in list(record.items()):
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, float) and value == int(value):
                        record[key] = int(value)
                
                record['_sheet'] = sheet
            
            all_records.extend(records)
            total += len(records)
            print(f"     Sheet '{sheet}': {len(records)} records, {len(df.columns)} columns")
        
        result = {
            'source': 'IPC 302 Case Documents',
            'filename': filename,
            'description': 'Court judgments and case documents related to IPC Section 302 (Murder) / BNS Section 103',
            'sheets': sheets,
            'columns': list(df.columns),
            'total_records': total,
            'records': all_records,
        }
        
        # Write output
        json_name = Path(filename).stem.replace(' ', '_') + '.json'
        output_path = os.path.join(output_dir, json_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        file_size = os.path.getsize(output_path)
        print(f"  [OK] Written: {json_name} ({total} records, {file_size:,} bytes)")
        
        return result
        
    except Exception as e:
        print(f"  [ERROR] {e}")
        return {'error': str(e)}


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(project_dir, 'DATASETS')
    output_dir = os.path.join(project_dir, 'BNS DATASET', 'output', 'case_docs')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  LegalCompass AI - IPC 302 Case Document Converter")
    print("=" * 60)
    
    # Find Excel files
    excel_files = list(Path(datasets_dir).glob('*.xlsx'))
    print(f"\n  Found {len(excel_files)} Excel files")
    
    for excel_file in excel_files:
        print(f"\n{'-' * 50}")
        convert_excel_to_json(str(excel_file), output_dir)
    
    print(f"\n{'=' * 60}")
    print(f"  Output directory: {output_dir}")
    print()


if __name__ == '__main__':
    main()
