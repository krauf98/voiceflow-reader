import pdfplumber
from pypdf import PdfReader
import os
import re
import unicodedata

def fix_reversed_arabic(text):
    """
    Classic/Fallback Fix: Reverses lines containing Arabic.
    Useful for pypdf which often extracts Visual RTL as LTR string.
    """
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        if arabic_pattern.search(line):
            fixed_lines.append(line[::-1])
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)

def parse_pdf_fallback(file_path):
    """
    Fallback extraction using pypdf.
    """
    print("Fallback: Using pypdf parser.")
    try:
        reader = PdfReader(file_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text = fix_reversed_arabic(text)
                full_text.append(text)
        
        normalized_text = unicodedata.normalize('NFKC', "\n".join(full_text))
        return normalized_text
    except Exception as e:
        print(f"Error parsing PDF with pypdf: {e}")
        return ""

def parse_pdf_plumber(file_path):
    """
    Detailed extraction using PDFPlumber (Slower, handles complex layouts).
    """
    try:
        full_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                words.sort(key=lambda w: (round(w['top'] / 8) * 8, -w['x1']))
                
                current_line_top = None
                lines = []
                current_line = []
                
                arabic_pattern = re.compile(r'[\u0600-\u06FF]')

                for word in words:
                    if arabic_pattern.search(word['text']):
                        word['text'] = word['text'][::-1]

                    word_top = round(word['top'] / 8) * 8
                    if current_line_top is None:
                        current_line_top = word_top
                    
                    if word_top != current_line_top:
                        lines.append(" ".join([w['text'] for w in current_line]))
                        current_line = []
                        current_line_top = word_top
                    
                    current_line.append(word)
                
                if current_line:
                    lines.append(" ".join([w['text'] for w in current_line]))
                    
                full_text.append("\n".join(lines))
        return "\n".join(full_text)
    except Exception as e:
        print(f"Plumber fallback failed: {e}")
        return ""

def parse_pdf(file_path):
    """
    Primary Entry Point.
    Strategy: FAST (pypdf) -> Quality Check -> SLOW (pdfplumber).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1. Try Fast Method (pypdf)
    print("Parsing with pypdf (Fast)...")
    try:
        text = parse_pdf_fallback(file_path) # Reusing the pypdf logic
        
        # 2. Quality Check
        is_garbage = False
        clean_text = text.replace(" ", "").replace("\n", "")
        if len(clean_text) > 50:
             n_ratio = (clean_text.count('n') + clean_text.count('N')) / len(clean_text)
             if n_ratio > 0.4:
                 is_garbage = True
                 print(f"Detected garbage in pypdf output ({n_ratio:.0%} 'n').")
        
        if not text.strip() or is_garbage:
             print("Fast parse unsatisfied. Switching to robust parser (pdfplumber)...")
             return parse_pdf_plumber(file_path)

        # Normalize and Return
        text = unicodedata.normalize('NFKC', text)
        print(f"Final Encoded Text Sample: {text[:100]}")
        return text

    except Exception as e:
        print(f"Fast parse error: {e}. Switching to robust parser...")
        return parse_pdf_plumber(file_path)
