import streamlit as st
from pathlib import Path
import time
import threading
from ..translator.core import Translator
from ..translator.utils import get_audio_html, validate_language
from ..translator.config import SUPPORTED_LANGUAGES, UI_SETTINGS

def initialize_session_state():
    """Initialize session state variables"""
    if 'translator' not in st.session_state:
        st.session_state.translator = None
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []
    if 'recording' not in st.session_state:
        st.session_state.recording = False

def setup_ui():
    """Configure the Streamlit UI"""
    st.set_page_config(
        page_title=UI_SETTINGS['page_title'],
        page_icon=UI_SETTINGS['page_icon'],
        layout=UI_SETTINGS['layout']
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .translation-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            margin: 10px 0;
            border-left: 4px solid #2e6fdf;
        }
        .timestamp {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 8px;
        }
        .stButton>button {
            width: 100%;
            background-color: #2e6fdf;
            color: white;
        }
        .stButton>button:hover {
            background-color: #1e4fa0;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    initialize_session_state()
    setup_ui()
    
    st.title("🌍 Real-Time Language Translator")
    st.markdown("Translate speech in real-time between multiple languages!")
    
    # Sidebar language selection
    st.sidebar.title("Settings")
    source_lang = st.sidebar.selectbox(
        "Source Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: SUPPORTED_LANGUAGES[x],
        index=list(SUPPORTED_LANGUAGES.keys()).index('en')
    )
    
    target_lang = st.sidebar.selectbox(
        "Target Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: SUPPORTED_LANGUAGES[x],
        index=list(SUPPORTED_LANGUAGES.keys()).index('fr')
    )
    
    # Initialize or update translator
    if (st.session_state.translator is None or 
        source_lang != st.session_state.translator.source_lang or 
        target_lang != st.session_state.translator.target_lang):
        st.session_state.translator = Translator(source_lang, target_lang)
    
    # Main content area
    output_container = st.empty()
    
    # Recording control
    if st.button("Start Recording" if not st.session_state.recording else "Stop Recording"):
        st.session_state.recording = not st.session_state.recording
        if st.session_state.recording:
            st.session_state.translator.start_listening()
        else:
            st.session_state.translator.stop_listening()
    
    # Clear history button
    if st.button("Clear History"):
        st.session_state.translation_history = []
    
    # Process audio queue
    if st.session_state.recording:
        process_audio_queue(output_container)
    
    # Display translation history
    display_translation_history()

def process_audio_queue(output_container):
    """Process audio from the queue and update display"""
    try:
        while not st.session_state.translator.audio_queue.empty():
            audio = st.session_state.translator.audio_queue.get_nowait()
            
            # Show recognition status
            output_container.text("Recognizing...")
            
            # Get translation
            result = st.session_state.translator.translate_audio(audio)
            
            if 'error' in result:
                output_container.error(result['error'])
                time.sleep(0.5)
                continue
            
            # Show results
            output_container.markdown(f"""
                ```
                You said: {result['original']}
                Translation: {result['translation']}
                ```
            """)
            
            # Generate audio in background
            threading.Thread(
                target=lambda: st.session_state.translator.generate_audio(result['translation']),
                daemon=True
            ).start()
            
            # Update history
            st.session_state.translation_history.append({
                **result,
                'timestamp': time.strftime('%H:%M:%S')
            })
            
            # Limit history size
            if len(st.session_state.translation_history) > UI_SETTINGS['max_history']:
                st.session_state.translation_history.pop(0)
                
    except Exception as e:
        output_container.error(f"Error: {str(e)}")

def display_translation_history():
    """Display the translation history"""
    if st.session_state.translation_history:
        st.markdown("---")
        st.subheader("📝 Translation History")
        
        for item in reversed(st.session_state.translation_history):
            with st.container():
                st.markdown(f"""
                    <div class="translation-box">
                        <p class="timestamp">{item['timestamp']}</p>
                        <p><strong>Original:</strong> {item['original']}</p>
                        <p><strong>Translation:</strong> {item['translation']}</p>
                        {'<p><em>(cached)</em></p>' if item.get('cached', False) else ''}
                    </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
