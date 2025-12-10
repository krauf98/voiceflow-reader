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

def parse_pdf(file_path):
    """
    Extracts text using PDFPlumber with custom Right-to-Left sorting for Arabic.
    Falls back to pypdf if output seems corrupted (e.g. CID font issues).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        full_text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                
                # Sort: Y (rounded) then -X (Right to Left)
                words.sort(key=lambda w: (round(w['top'] / 8) * 8, -w['x1']))
                
                # Group into lines
                current_line_top = None
                lines = []
                current_line = []
                
                arabic_pattern = re.compile(r'[\u0600-\u06FF]')

                for word in words:
                    # Fix reversed letters within word if Arabic
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
        
        extracted_text = "\n".join(full_text)

        # Quality Check: If text is mostly "n" or "N" (common placeholder corruption)
        # Or if text is suspiciously short but file size is large.
        clean_text = extracted_text.replace(" ", "").replace("\n", "")
        if len(clean_text) > 50:
             n_ratio = (clean_text.count('n') + clean_text.count('N')) / len(clean_text)
             # If > 40% of chars are 'n', it's likely garbage
             if n_ratio > 0.4:
                 print(f"Detected garbage text ({n_ratio:.0%} 'n'). Switching to fallback.")
                 return parse_pdf_fallback(file_path)

        if not extracted_text.strip():
             print("Extracted text empty. Switching to fallback.")
             return parse_pdf_fallback(file_path)

        # Normalize to fix display issues (squares)
        extracted_text = unicodedata.normalize('NFKC', extracted_text)

        # Debug: Print sample to verify valid chars
        print(f"Final Extracted Text Sample: {extracted_text[:100]}")
        return extracted_text

    except Exception as e:
        print(f"Error parsing PDF with pdfplumber: {e}")
        return parse_pdf_fallback(file_path)
