import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import queue
import threading
from pathlib import Path
import tempfile
import time
from .utils import cleanup_old_files
from .config import SUPPORTED_LANGUAGES, SPEECH_SETTINGS

class Translator:
    """Core translator class handling speech recognition and translation"""
    
    def __init__(self, source_lang='en', target_lang='fr'):
        """Initialize the translator with language settings"""
        if source_lang not in SUPPORTED_LANGUAGES or target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language. Must be one of: {', '.join(SUPPORTED_LANGUAGES.keys())}")
            
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        self.recognizer = self._setup_recognizer()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.temp_dir = Path(tempfile.mkdtemp())
        self.translation_cache = {}
        
    def _setup_recognizer(self):
        """Configure speech recognizer with optimal settings"""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = SPEECH_SETTINGS['energy_threshold']
        recognizer.dynamic_energy_threshold = SPEECH_SETTINGS['dynamic_energy_threshold']
        recognizer.pause_threshold = SPEECH_SETTINGS['pause_threshold']
        return recognizer
        
    def start_listening(self):
        """Start the listening thread"""
        self.is_listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()
        
    def stop_listening(self):
        """Stop the listening thread"""
        self.is_listening = False
        cleanup_old_files(self.temp_dir)
        
    def _listen_thread(self):
        """Background thread for audio capture"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=SPEECH_SETTINGS['timeout'],
                            phrase_time_limit=SPEECH_SETTINGS['phrase_time_limit']
                        )
                        self.audio_queue.put(audio)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"Listening error: {e}")
                        time.sleep(0.5)
        except Exception as e:
            print(f"Microphone error: {e}")
            
    def translate_audio(self, audio):
        """Translate audio input to target language"""
        try:
            text = self.recognizer.recognize_google(audio, language=self.source_lang)
            
            # Check cache
            if text in self.translation_cache:
                return {
                    'original': text,
                    'translation': self.translation_cache[text],
                    'cached': True
                }
                
            translation = self.translator.translate(text)
            self.translation_cache[text] = translation
            
            return {
                'original': text,
                'translation': translation,
                'cached': False
            }
            
        except sr.UnknownValueError:
            return {'error': 'Could not understand audio'}
        except sr.RequestError as e:
            return {'error': f'Service error: {str(e)}'}
        except Exception as e:
            return {'error': f'Translation error: {str(e)}'}
            
    def generate_audio(self, text):
        """Generate audio file for translated text"""
        try:
            audio_path = self.temp_dir / f"audio_{time.time()}.mp3"
            tts = gTTS(text=text, lang=self.target_lang)
            tts.save(str(audio_path))
            return audio_path
        except Exception as e:
            print(f"Audio generation error: {e}")
            return None 
