import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def default_serializer(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    iltur_dir = os.path.join(base_dir, 'BNS DATASET', 'IL-TUR')
    output_dir = os.path.join(base_dir, 'BNS DATASET', 'output')
    
    if not os.path.exists(iltur_dir):
        print(f"IL-TUR directory not found at {iltur_dir}")
        return
        
    print("=" * 60)
    print("  Converting IL-TUR Parquet to JSON")
    print("=" * 60)
    
    for root, dirs, files in os.walk(iltur_dir):
        for file in files:
            if file.endswith('.parquet'):
                task_type = os.path.basename(root)
                filepath = os.path.join(root, file)
                print(f"Reading {task_type}/{file}...")
                
                try:
                    df = pd.read_parquet(filepath)
                    
                    # Sample up to 5000 rows to keep JSON manageable and fast
                    if len(df) > 5000:
                        df = df.sample(5000, random_state=42)
                    
                    records = df.to_dict(orient='records')
                    
                    # Write to JSON
                    out_name = f"ILTUR_{task_type}_{file.replace('.parquet', '.json')}"
                    out_path = os.path.join(output_dir, out_name)
                    
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(records, f, ensure_ascii=False, default=default_serializer)
                    print(f"  -> Saved {out_name} ({len(records)} records)")
                except Exception as e:
                    print(f"  -> Failed to read {file}: {e}")

if __name__ == '__main__':
    main()
