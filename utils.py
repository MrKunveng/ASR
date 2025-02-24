import time
from pathlib import Path
import base64

def cleanup_old_files(directory: Path, max_age: int = 3600):
    """Remove temporary files older than max_age seconds"""
    current_time = time.time()
    for file in directory.glob("*.mp3"):
        if current_time - file.stat().st_mtime > max_age:
            try:
                file.unlink()
            except Exception:
                pass

def get_audio_html(audio_path: Path) -> str:
    """Convert audio file to HTML playable format"""
    try:
        audio_file = open(audio_path, 'rb')
        audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        return f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
    except Exception as e:
        print(f"Error creating audio HTML: {e}")
        return ""

def validate_language(lang: str, supported_languages: dict) -> bool:
    """Validate if a language is supported"""
    return lang in supported_languages 
