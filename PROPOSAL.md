# Project Proposal: Python PDF-to-Voice Application

## 1. Project Overview
This application will allow users to upload PDF documents, extract text (including support for scanned PDFs via OCR), and convert that text into high-quality speech. It features a modern, premium web interface with dark mode, playback controls, and text highlighting.

## 2. Technology Stack Recommendation

### Backend (Python)
- **Framework**: **Flask**. It is lightweight, flexible, and perfect for wrapping the PDF/TTS logic into an API.
- **PDF Parsing**: 
  - **`pdfminer.six`**: For robust text extraction from standard PDFs.
  - **`ocrmypdf` / `Tesseract`**: For scanned documents (optional advanced feature).
- **Text-to-Speech**: 
  - **`edge-tts`**: Highly recommended for free, high-quality, natural-sounding neural voices (requires internet).
  - **`gTTS`**: Google Text-to-Speech as a backup.
- **Language Detection**: **`langdetect`** library.

### Frontend (Web)
- **Core**: HTML5, CSS3 (Custom Premium Design), JavaScript (Vanilla ES6+).
- **Styling**: Custom CSS variables for easy theming (Dark Mode default).
- **Architecture**: Single Page Application (SPA) feel, communicating with the Flask API.

### Mobile
- **Framework**: **React Native** or **Flutter**. Both can easily consume the Flask API.
- **Recommendation**: React Native if you are familiar with JavaScript; Flutter for a highly polished native feel out-of-the-box.

## 3. Python Project Structure

```text
py-pdf-voice/
├── backend/
│   ├── app.py                # Main Flask Application
│   ├── requirements.txt      # Python Dependencies
│   └── services/
│       ├── __init__.py
│       ├── pdf_parser.py     # Handles PDF loading and text extraction
│       ├── tts_engine.py     # Interface for TTS services (EdgeTTS/gTTS)
│       └── lang_manager.py   # Language detection and voice mapping
├── frontend/
│   ├── index.html            # Main User Interface
│   ├── css/
│   │   └── style.css         # Premium Dark Mode Styles
│   ├── js/
│   │   └── app.js            # Frontend Logic (Upload, Player, Highlight)
│   └── assets/               # Icons/Images
└── README.md
```

## 4. Key Code Snippets

### A. Loading and Parsing a PDF
Using `pdfminer.six` for better text extraction accuracy.

```python
from pdfminer.high_level import extract_text

def parse_pdf(file_path):
    """
    Extracts text from a PDF file.
    """
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
```

### B. Text-to-Speech Service (Multilingual)
Using `edge-tts` for natural voices.

```python
import edge_tts
import asyncio

# Map languages to specific Edge TTS voices
VOICE_MAP = {
    'en': 'en-US-ChristopherNeural', # English
    'es': 'es-ES-AlvaroNeural',      # Spanish
    'fr': 'fr-FR-HenriNeural',       # French
    'de': 'de-DE-ConradNeural',      # German
    'zh': 'zh-CN-YunxiNeural'        # Mandarin
}

async def generate_audio(text, lang_code, output_file):
    """
    Generates audio from text using the appropriate voice for the language.
    """
    voice = VOICE_MAP.get(lang_code, 'en-US-ChristopherNeural')
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file
```

### C. Language Detection
```python
from langdetect import detect

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en' # Default to English
```
