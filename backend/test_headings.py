from pypdf import PdfReader
from pathlib import Path
import re

def detect_sections(text: str, file_type: str = ".pdf") -> list[tuple[str, int, int]]:
    """Detect sections based on file type with tightened heuristics."""
    sections = []
    
    if file_type == ".md":
        # Markdown syntax
        for line_num, line in enumerate(text.split('\n')):
            line = line.strip()
            if line.startswith('# '):
                sections.append((line[2:].strip(), 1, line_num))
            elif line.startswith('## '):
                sections.append((line[3:].strip(), 2, line_num))
            elif line.startswith('### '):
                sections.append((line[4:].strip(), 3, line_num))
    
    elif file_type in {".pdf", ".txt"}:
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Numbered sections: "3.1 Section Name"
            if re.match(r'^\d+\.\d+\s+[A-Z]', line):
                sections.append((line, 2, line_num))
            # Chapter/Section keywords
            elif re.match(r'^(Chapter|Section|Unit)\s+\d+', line, re.IGNORECASE):
                sections.append((line, 1, line_num))
            # All-caps lines with tightened rules:
            # - Must be 2+ words (filter out single-word artifacts)
            # - Length between 5 and 80 chars (filter out logos/footers)
            # - Must be followed by body text (not another short line)
            elif line.isupper() and len(line.split()) >= 2 and 5 <= len(line) <= 80:
                # Check if next line has substantial content
                if line_num + 1 < len(lines):
                    next_line = lines[line_num + 1].strip()
                    if len(next_line) > 20:  # Next line has substantial content
                        sections.append((line, 1, line_num))
    
    elif file_type == ".docx":
        # Would need to parse the actual DOCX structure
        # For now, use same heuristics as PDF
        pass
    
    return sections

# Test on actual Unit-3.pdf (file has hyphen, DB has space)
unit3_pdf = Path('storage/uploads/2f9c2a2c-2dac-4596-b117-6b2cffe01425/1ca098903c93137b-Unit-3.pdf')
ml_cheatsheet = Path('storage/uploads/2f9c2a2c-2dac-4596-b117-6b2cffe01425/58623835d9e8cb00-machine-learning-cheat-sheet.pdf')

def test_pdf(pdf_path, name):
    if pdf_path.exists():
        print(f'\n--- Testing on {name} ---')
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            # Extract text from first 5 pages
            full_text = ""
            for i in range(min(5, len(reader.pages))):
                full_text += reader.pages[i].extract_text() or ""
                full_text += "\n\n"
            
            print(f'Total extracted text length: {len(full_text)} chars')
            print(f'Number of pages: {len(reader.pages)}')
            print('\n--- First 1000 chars of extracted text ---')
            print(full_text[:1000])
            print('...\n')
            
            print('--- Sections detected ---')
            sections = detect_sections(full_text, ".pdf")
            print(f'Found {len(sections)} sections')
            for section, level, line_num in sections:
                print(f'  Line {line_num} H{level}: {section[:80]}...' if len(section) > 80 else f'  Line {line_num} H{level}: {section}')
    else:
        print(f'{name} not found at: {pdf_path}')

test_pdf(unit3_pdf, "Unit-3.pdf")
test_pdf(ml_cheatsheet, "machine-learning-cheat-sheet.pdf")
