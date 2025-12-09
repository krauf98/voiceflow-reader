import edge_tts
import os
import asyncio
from gtts import gTTS

# Voice mapping for common languages
VOICE_MAP = {
    'en': 'en-US-ChristopherNeural',
    'es': 'es-ES-AlvaroNeural',
    'fr': 'fr-FR-HenriNeural',
    'de': 'de-DE-ConradNeural',
    'zh': 'zh-CN-YunxiNeural',
    'it': 'it-IT-DiegoNeural',
    'pt': 'pt-BR-AntonioNeural',
    'ar': 'ar-EG-SalmaNeural'
}

try:
    import pyttsx3
    SYSTEM_TTS_AVAILABLE = True
except ImportError:
    SYSTEM_TTS_AVAILABLE = False

async def generate_audio_async(text, lang_code, output_file, rate="+0%"):
    voice = VOICE_MAP.get(lang_code, 'en-US-ChristopherNeural')
    # Debug logging
    print(f"TTS Request: Voice={voice}, Rate={rate}, TextLen={len(text)}")
    
    if not text or not text.strip():
        print("Error: Empty text provided to TTS")
        return output_file 
    
    # edge-tts check: omit rate if default to avoid potential issues
    if rate == "+0%":
        communicate = edge_tts.Communicate(text, voice)
    else:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        
    # verify directory exists again just in case
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "error":
                print(f"TTS Stream Error: {chunk}")
                raise Exception(f"EdgeTTS Stream Error: {chunk}")
    
    return output_file

def generate_audio_google(text, lang_code, output_file):
    """
    Google Translate TTS (HTTP based).
    """
    print("Using Google TTS...")
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_file)
        return output_file, None
    except Exception as e:
        print(f"Google TTS failed: {e}")
        return None, str(e)

def generate_audio_system(text, lang_code, output_file):
    """
    Offline System TTS (pyttsx3).
    Matches language code to installed system voices.
    """
    if not SYSTEM_TTS_AVAILABLE:
        print("System TTS not available (usually due to Cloud environment).")
        return None, "System TTS is not supported on this server. Please use Edge or Google."

    print(f"Using System TTS for language: {lang_code}...")
    try:
        engine = pyttsx3.init()
        
        # Voice Selection Logic
        voices = engine.getProperty('voices')
        selected_voice = None
        
        # Simplified language mapping for search
        lang_search_map = {
            'ar': ['Arabic', 'Hoda', 'Naayf'],
            'en': ['English', 'David', 'Zira', 'US'],
            'es': ['Spanish', 'Helena', 'Sabina'],
            'fr': ['French', 'Hortense', 'Julie'],
            'de': ['German', 'Hedda', 'Stefan'],
            'zh': ['Chinese', 'Huihui', 'Kangkang']
        }
        
        search_terms = lang_search_map.get(lang_code, ['English'])
        
        for voice in voices:
            # Check if any search term is in the voice name or ID
            if any(term.lower() in voice.name.lower() for term in search_terms):
                selected_voice = voice
                break
        
        if selected_voice:
            print(f"System TTS: Selected voice '{selected_voice.name}'")
            engine.setProperty('voice', selected_voice.id)
        else:
            print(f"System TTS: No voice found for '{lang_code}', using default.")

        engine.save_to_file(text, output_file)
        engine.runAndWait()
        return output_file, None
    except Exception as e:
        print(f"System TTS failed: {e}")
        return None, str(e)

def generate_audio(text, lang_code, output_file, speed=1.0, engine='edge'):
    """
    Synchronous wrapper for generating audio with multiple engine support.
    Engines: 'edge' (default), 'google', 'system'.
    """
    # Sanitize text
    if text:
        text = text.replace('\0', '').strip()
    
    if engine == 'google':
        return generate_audio_google(text, lang_code, output_file)
    
    if engine == 'system':
        return generate_audio_system(text, lang_code, output_file)

    # Default: Edge TTS
    # Convert float speed to percentage string
    percentage = int((speed - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"

    try:
        # Try Edge TTS First
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_audio_async(text, lang_code, output_file, rate=rate_str))
        loop.close()
        
        # Verify file size - if 0 bytes, consider it failed
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            return output_file, None
        else:
            raise Exception("EdgeTTS produced empty file")

    except Exception as e:
        print(f"Primary TTS failed ({e}), switching to Google fallback...")
        return generate_audio_google(text, lang_code, output_file)
