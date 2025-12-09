from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import uuid
from services.pdf_parser import parse_pdf
from services.tts_engine import generate_audio
from langdetect import detect

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
AUDIO_FOLDER = os.path.join(BASE_DIR, 'audio_cache')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Extract Text
        text = parse_pdf(filepath)
        
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'}), 500

        # Detect Language (simple generic detection on first 500 chars)
        try:
            detected_lang = detect(text[:500])
        except:
            detected_lang = 'en'

        return jsonify({
            'success': True,
            'text': text,
            'language': detected_lang,
            'filename': filename
        })

@app.route('/api/synthesize', methods=['POST'])
def synthesize_audio():
    data = request.json
    text = data.get('text')
    lang = data.get('language', 'en')
    speed = float(data.get('speed', 1.0))
    engine = data.get('engine', 'edge')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Create a unique filename for this audio snippet
    # Using hash of text+speed+lang might be better for caching, using uuid for now
    audio_filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(AUDIO_FOLDER, audio_filename)

    result_path, error_msg = generate_audio(text, lang, output_path, speed, engine=engine)

    if result_path and os.path.exists(result_path):
        return jsonify({
            'success': True,
            'audio_url': f"/audio/{audio_filename}"
        })
    else:
        return jsonify({'error': f'TTS Generation failed: {error_msg}'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == '__main__':
    # Run on 0.0.0.0 to allow access from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
