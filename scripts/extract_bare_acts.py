"""
LegalCompass AI - Bare Act PDF Extractor (v2)
Improved section detection for Indian Gazette PDF formatting.

Key insight: In gazette PDFs, section numbers appear as "4.The" (no space),
at the beginning of lines after newlines.
"""

import json
import re
import sys
import os
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("ERROR: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)


# ── Acts configuration ────────────────────────────────────────────────────

ACTS_CONFIG = {
    'BNS': {
        'full_name': 'Bharatiya Nyaya Sanhita, 2023',
        'short_name': 'BNS',
        'act_number': '45 of 2023',
        'pdf_file': 'THE BHARATIYA NYAYA SANHITA, 2023.pdf',
        'total_sections': 358,
    },
    'BNSS': {
        'full_name': 'Bharatiya Nagarik Suraksha Sanhita, 2023',
        'short_name': 'BNSS',
        'act_number': '46 of 2023',
        'pdf_file': 'THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023.pdf',
        'total_sections': 531,
    },
    'BSA': {
        'full_name': 'Bharatiya Sakshya Adhiniyam, 2023',
        'short_name': 'BSA',
        'act_number': '47 of 2023',
        'pdf_file': 'THE BHARATIYA SAKSHYA ADHINIYAM, 2023.pdf',
        'total_sections': 170,
    },
}

# Known chapter definitions per Act (fallback for when chapter detection from text is incomplete)
BNS_CHAPTERS = {
    'I': 'PRELIMINARY',
    'II': 'OF PUNISHMENTS',
    'III': 'GENERAL EXCEPTIONS',
    'IV': 'OF ABETMENT, CRIMINAL CONSPIRACY AND ATTEMPT',
    'V': 'OF OFFENCES AGAINST WOMAN AND CHILD',
    'VI': 'OF OFFENCES AFFECTING THE HUMAN BODY',
    'VII': 'OF OFFENCES AGAINST PROPERTY',
    'VIII': 'OF OFFENCES RELATING TO DOCUMENTS AND TO PROPERTY MARKS',
    'IX': 'OF OFFENCES RELATING TO CURRENCY NOTES AND BANK NOTES',
    'X': 'OF OFFENCES RELATING TO THE STATE',
    'XI': 'OF OFFENCES RELATING TO THE ARMED FORCES',
    'XII': 'OF OFFENCES RELATING TO ELECTIONS',
    'XIII': 'OF OFFENCES AFFECTING THE PUBLIC TRANQUILLITY',
    'XIV': 'OF OFFENCES BY OR RELATING TO PUBLIC SERVANTS',
    'XV': 'OF OFFENCES RELATING TO PUBLIC JUSTICE',
    'XVI': 'OF OFFENCES AFFECTING PUBLIC HEALTH, SAFETY, CONVENIENCE, DECENCY AND MORALS',
    'XVII': 'OF CRIMINAL INTIMIDATION, INSULT AND ANNOYANCE',
}

# Simple noise lines to remove (exact or substring match)
NOISE_SUBSTRINGS = [
    'THE GAZETTE OF INDIA EXTRAORDINARY',
    'xxxGIDHxxx', 'xxxGIDExxx',
    'PUBLISHED BY AUTHORITY',
    'MINISTRY OF LAW AND JUSTICE',
    'MINISTRY OF LAWAND JUSTICE',
    '(Legislative Department)',
    'Separate paging is given',
    'REGISTERED NO. DL',
    'CG-DL-E-',
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return '\n'.join(pages_text)


def clean_text(text: str) -> str:
    """Remove gazette noise from extracted text."""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            cleaned_lines.append('')
            continue
        
        # Skip noise lines
        skip = False
        for noise in NOISE_SUBSTRINGS:
            if noise in stripped:
                skip = True
                break
        if skip:
            continue
        
        # Skip pure underscore lines
        if re.match(r'^[_\-=]{5,}$', stripped):
            continue
        
        # Skip gazette Hindi transliteration noise
        if re.match(r'^[vlkHIiPp/kkjk]', stripped) and len(stripped) < 30 and not any(c.isdigit() for c in stripped):
            continue
        
        # Skip page numbers that are standalone
        if re.match(r'^\d{1,3}$', stripped):
            continue
        
        # Skip "[Part II--" type markers
        if re.match(r'^\[Part\s+II', stripped):
            continue
        
        # Skip "Sec. 1]" markers
        if re.match(r'^Sec\.\s+\d+\]', stripped):
            continue
            
        cleaned_lines.append(stripped)
    
    # Collapse multiple empty lines
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def find_chapter_at_position(text: str, pos: int, chapters_list: list) -> dict:
    """Find the chapter that contains a given text position."""
    current = {'number': '', 'title': ''}
    for ch in chapters_list:
        if ch['pos'] <= pos:
            current = ch
        else:
            break
    return current


def detect_chapters(text: str) -> list:
    """Detect chapter boundaries in the text."""
    chapters = []
    
    # Pattern: "CHAPTER" followed by roman or arabic numeral, then title on same/next line
    # Also handle "CHAPTERVI" (no space) as seen in gazette PDFs
    pattern = re.compile(
        r'(?:^|\n)\s*CHAPTER\s*([IVXLCDM]+|\d+)\s*\n\s*([A-Z][A-Z\s,\-\'\u2014AND]+?)(?:\n|$)',
        re.MULTILINE
    )
    
    for m in pattern.finditer(text):
        chapters.append({
            'number': m.group(1).strip(),
            'title': m.group(2).strip().rstrip('.'),
            'pos': m.start(),
        })
    
    # Also look for "PART I", "PART II" style (used in BSA)
    part_pattern = re.compile(
        r'(?:^|\n)\s*PART\s+([IVXLCDM]+|\d+)\s*\n',
        re.MULTILINE
    )
    for m in part_pattern.finditer(text):
        chapters.append({
            'number': f"Part {m.group(1).strip()}",
            'title': '',
            'pos': m.start(),
        })
    
    chapters.sort(key=lambda x: x['pos'])
    return chapters


def extract_section_title(full_text: str) -> str:
    """Extract a meaningful title from the section text."""
    # Get first meaningful line
    first_line = full_text.split('\n')[0].strip()
    
    # Remove the section number prefix
    first_line = re.sub(r'^\d+\.\s*', '', first_line)
    
    # If there's a dash separator, take the part before it as title
    dash_match = re.match(r'^(.*?)[\u2014\u2013\-]{1,2}\s*', first_line)
    if dash_match and len(dash_match.group(1).strip()) > 3:
        return dash_match.group(1).strip().rstrip('.')
    
    # Take up to the first period or opening parenthesis
    title_match = re.match(r'^(.*?)(?:\.\s|\(\d+\))', first_line)
    if title_match and len(title_match.group(1).strip()) > 3:
        title = title_match.group(1).strip()
        if len(title) > 200:
            title = title[:200].rsplit(' ', 1)[0] + '...'
        return title.rstrip('.')
    
    # Fallback: first 150 chars of first line
    title = first_line[:150].strip()
    if len(first_line) > 150:
        title = title.rsplit(' ', 1)[0] + '...'
    return title.rstrip('.')


def extract_cross_references(text: str, current_act: str) -> list:
    """Extract references to other sections/acts."""
    refs = set()
    
    section_refs = re.findall(r'section\s+(\d+)', text, re.IGNORECASE)
    for ref in section_refs:
        refs.add(f"{current_act} S{ref}")
    
    act_map = {
        'Bharatiya Nyaya Sanhita': 'BNS',
        'Bharatiya Nagarik Suraksha Sanhita': 'BNSS',
        'Bharatiya Sakshya Adhiniyam': 'BSA',
    }
    for act_name, act_short in act_map.items():
        if act_short != current_act and act_name.lower() in text.lower():
            refs.add(f"Ref:{act_short}")
    
    return sorted(list(refs))


def remove_marginal_notes(text: str) -> str:
    """Remove marginal notes that appear as side annotations in gazette text."""
    # Marginal notes are typically short phrases at the end of lines that describe the section
    # They appear after the actual section text. Common patterns:
    marginal_patterns = [
        r'Short title,?\s*\n?commencement\s*\n?and\s*\n?application\.',
        r'Definitions?\.\n',
        r'General\s+explanations?\.\n',
        r'Punishments?\.\n',
        r'Commutation\s+of\s+sentence\.\n',
        r'\d+\s+of\s+\d{4}\.\n',  # Act references like "40 of 2019."
    ]
    for pat in marginal_patterns:
        text = re.sub(pat, '\n', text, flags=re.IGNORECASE)
    return text


def parse_act(raw_text: str, config: dict) -> list:
    """Parse full text of an Act into sections."""
    cleaned = clean_text(raw_text)
    chapters = detect_chapters(cleaned)
    
    # Find all section boundaries
    # Section starts: number followed by period, at start of line
    # Can be "4.The" or "4. The" or "4.(1)"
    section_pattern = re.compile(r'(?:^|\n)(\d+)\.([\s\S])', re.MULTILINE)
    
    # Collect all potential section starts
    starts = []
    for m in section_pattern.finditer(cleaned):
        sec_num = int(m.group(1))
        # Filter out false positives:
        # - Ignore if the number is > total_sections + 10
        # - Ignore sub-references inside text (like "section 302.")
        if sec_num <= config['total_sections'] + 10:
            starts.append({
                'num': sec_num,
                'pos': m.start(),
                'match_end': m.end(),
            })
    
    # Remove duplicates (keep the one that makes sequential sense)
    # If we see [1, 2, 3, 2, 4], the second '2' is likely a false positive
    filtered_starts = []
    seen_sections = set()
    for s in starts:
        if s['num'] not in seen_sections:
            filtered_starts.append(s)
            seen_sections.add(s['num'])
        else:
            # Check if this is a better match (e.g., coming after a higher-numbered section)
            pass  # Keep first occurrence
    
    starts = filtered_starts
    
    # Now extract text between consecutive section starts
    sections = []
    for i, start in enumerate(starts):
        sec_num = start['num']
        begin = start['pos']
        
        # Find end: next section start or end of text
        if i + 1 < len(starts):
            end = starts[i + 1]['pos']
        else:
            end = len(cleaned)
        
        sec_text = cleaned[begin:end].strip()
        
        # Clean the text
        sec_text = remove_marginal_notes(sec_text)
        sec_text = re.sub(r'\n{3,}', '\n\n', sec_text).strip()
        
        # Get chapter info
        chapter = find_chapter_at_position(cleaned, begin, chapters)
        
        # Extract title
        title = extract_section_title(sec_text)
        
        # Count illustrations and explanations
        illus_count = len(re.findall(r'Illustration[s]?\.', sec_text))
        expl_count = len(re.findall(r'Explanation[\s\d]*[\.\u2014\-]', sec_text))
        
        # Cross-references
        xrefs = extract_cross_references(sec_text, config['short_name'])
        
        section = {
            'id': f"{config['short_name']}_2023_S{str(sec_num).zfill(3)}",
            'act': config['full_name'],
            'act_short': config['short_name'],
            'act_number': config['act_number'],
            'chapter_number': chapter['number'],
            'chapter_title': chapter['title'],
            'section_number': str(sec_num),
            'section_title': title,
            'language': 'English',
            'text': sec_text,
            'has_illustrations': illus_count > 0,
            'has_explanations': expl_count > 0,
            'illustration_count': illus_count,
            'explanation_count': expl_count,
            'cross_references': xrefs,
            'source_pdf': config['pdf_file'],
        }
        
        sections.append(section)
    
    return sections, cleaned


def process_act(base_dir: str, act_key: str, output_dir: str) -> dict:
    """Process a single Act and produce JSON."""
    config = ACTS_CONFIG[act_key]
    pdf_path = os.path.join(base_dir, config['pdf_file'])
    
    if not os.path.exists(pdf_path):
        print(f"  [ERROR] PDF not found: {pdf_path}")
        return None
    
    print(f"  [READ] Reading PDF: {config['pdf_file']}")
    raw_text = extract_text_from_pdf(pdf_path)
    num_pages = len(PdfReader(pdf_path).pages)
    print(f"     Extracted {len(raw_text):,} characters from {num_pages} pages")
    
    print(f"  [PARSE] Parsing sections...")
    sections, cleaned_text = parse_act(raw_text, config)
    
    found = len(sections)
    expected = config['total_sections']
    pct = (found / expected) * 100
    print(f"     Found {found}/{expected} sections ({pct:.1f}%)")
    
    # Identify missing sections
    found_nums = set(int(s['section_number']) for s in sections)
    missing = [i for i in range(1, expected + 1) if i not in found_nums]
    if missing:
        print(f"     Missing sections ({len(missing)}): {missing[:20]}{'...' if len(missing) > 20 else ''}")
    
    # Build output
    output = {
        'metadata': {
            'act': config['full_name'],
            'act_short': config['short_name'],
            'act_number': config['act_number'],
            'language': 'English',
            'source_pdf': config['pdf_file'],
            'total_sections_found': found,
            'total_sections_expected': expected,
            'extraction_coverage': round(pct, 1),
            'missing_sections': missing,
        },
        'sections': sections,
    }
    
    # Write output
    output_path = os.path.join(output_dir, f"{act_key}_structured.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(output_path)
    print(f"  [OK] Written: {act_key}_structured.json ({file_size:,} bytes)")
    
    # Stats
    ch_count = len(set((s['chapter_number'], s['chapter_title']) for s in sections if s['chapter_number']))
    illus = sum(1 for s in sections if s['has_illustrations'])
    xrefs = sum(1 for s in sections if s['cross_references'])
    print(f"  [STATS] Chapters: {ch_count} | With illustrations: {illus} | With cross-refs: {xrefs}")
    
    return output


def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'BNS DATASET')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("  LegalCompass AI - Bare Act Extractor v2")
    print("=" * 60)
    
    results = {}
    for act_key in ['BNS', 'BNSS', 'BSA']:
        print(f"\n{'-' * 60}")
        print(f"  Processing: {ACTS_CONFIG[act_key]['full_name']}")
        print(f"{'-' * 60}")
        
        result = process_act(base_dir, act_key, output_dir)
        if result:
            meta = result['metadata']
            results[act_key] = {
                'found': meta['total_sections_found'],
                'expected': meta['total_sections_expected'],
                'coverage': meta['extraction_coverage'],
                'missing': len(meta['missing_sections']),
            }
    
    # Final report
    print(f"\n{'=' * 60}")
    print("  EXTRACTION REPORT")
    print(f"{'=' * 60}")
    for act_key, r in results.items():
        status = "[OK]" if r['coverage'] >= 90 else "[WARN]"
        print(f"  {status} {act_key}: {r['found']}/{r['expected']} ({r['coverage']}%) - {r['missing']} missing")
    print()


if __name__ == '__main__':
    main()
