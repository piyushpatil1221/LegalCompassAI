"""
Debug script - dump raw and cleaned text from BNS PDF to understand section patterns.
"""
import re
import sys
sys.path.insert(0, '.')
from scripts.extract_bare_acts import extract_text_from_pdf, clean_gazette_noise

pdf_path = r"BNS DATASET\THE BHARATIYA NYAYA SANHITA, 2023.pdf"
raw = extract_text_from_pdf(pdf_path)
cleaned = clean_gazette_noise(raw)

# Save cleaned text for analysis
with open('BNS DATASET/output/_debug_bns_cleaned.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned)

print(f"Raw: {len(raw):,} chars")
print(f"Cleaned: {len(cleaned):,} chars")

# Find all lines that start with a number followed by period
section_starts = re.findall(r'(?:^|\n)\s*(\d+)\.\s', cleaned)
print(f"\nSection starts found: {len(section_starts)}")
print(f"Unique sections: {len(set(section_starts))}")
print(f"Sections: {sorted(set(int(s) for s in section_starts))[:30]}...")
print(f"Max section: {max(int(s) for s in section_starts)}")

# Show a sample around section 100 to see the pattern
pos = cleaned.find('\n100.')
if pos == -1:
    pos = cleaned.find('100.')
if pos >= 0:
    print(f"\n--- Around section 100 ---")
    print(cleaned[pos-100:pos+300])
else:
    print("\nSection 100 not found with pattern '100.'")
    # Search alternative patterns
    for pattern in ['\n100 ', '100.', ' 100.']:
        pos = cleaned.find(pattern)
        if pos >= 0:
            print(f"\nFound '{pattern}' at pos {pos}:")
            print(cleaned[pos-50:pos+200])
            break
