import streamlit as st
from deep_translator import GoogleTranslator
import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time
import tempfile

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        
    def play_text(self, text, lang='en'):
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
                
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(temp_filename)
            
            # Play audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Cleanup
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
            
        except Exception as e:
            st.error(f"Audio playback error: {str(e)}")

def translate_text(text, src_lang, dest_lang, retries=3):
    """Enhanced translation with better error handling and retries"""
    if not text:
        return None
        
    for attempt in range(retries):
        try:
            translator = GoogleTranslator(source=src_lang, target=dest_lang)
            translation = translator.translate(text)
            
            if translation:
                return translation
                
        except Exception as e:
            if attempt == retries - 1:
                st.error(f"Translation failed: {str(e)}")
                return None
            time.sleep(1)
            continue
            
    return None

def initialize_recognizer():
    """Initialize speech recognizer"""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 4000
    return recognizer

def recognize_speech(recognizer, source):
    """Recognize speech from microphone"""
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.warning("Could not understand audio")
        return None
    except sr.RequestError:
        st.error("Could not request results from speech recognition service")
        return None
    except Exception as e:
        st.error(f"Speech recognition error: {str(e)}")
        return None

def main():
    st.title("VerbalLink: Global Voice Bridge")
    st.markdown("##### Interactive Multilingual Conversation Companion")
    
    if 'audio_player' not in st.session_state:
        st.session_state.audio_player = AudioPlayer()
        
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []
        
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
        
    # Language mappings
    languages = {
        'English': 'en',
        'Hindi': 'hi',
        'Bengali': 'bn',
        'Telugu': 'te',
        'Marathi': 'mr',
        'Tamil': 'ta',
        'Urdu': 'ur',
        'Gujarati': 'gu',
        'Kannada': 'kn',
        'Malayalam': 'ml',
        'Punjabi': 'pa',
        'Assamese': 'as',
        'Sanskrit': 'sa',
        'Nepali': 'ne',
        'French': 'fr',
        'Spanish': 'es',
        'German': 'de',
        'Italian': 'it',
        'Japanese': 'ja',
        'Korean': 'ko',
        'Chinese': 'zh'
    }
    
    language_category = st.radio(
        "Language Category",
        ["All Languages", "Indian Languages Only"],
        horizontal=True
    )
    
    indian_languages = {k: v for k, v in languages.items() if v in 
                       ['hi', 'bn', 'te', 'mr', 'ta', 'ur', 'gu', 'kn', 'ml', 'pa', 'as', 'sa', 'ne']}
    
    display_languages = languages if language_category == "All Languages" else indian_languages
    
    source_lang = st.selectbox("Select source language:", list(display_languages.keys()))
    target_lang = st.selectbox("Select target language:", list(display_languages.keys()))
    
    # Add tabs for different input methods
    tab1, tab2 = st.tabs(["Text Input", "Voice Input"])
    
    with tab1:
        # Text input for translation
        text_input = st.text_area("Enter text to translate:", key="text_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Translate Text", key="text_translate"):
                if text_input:
                    try:
                        src_code = languages[source_lang]
                        dest_code = languages[target_lang]
                        
                        translation = translate_text(
                            text_input,
                            src_lang=src_code,
                            dest_lang=dest_code
                        )
                        
                        if translation:
                            # Add to history
                            st.session_state.translation_history.append({
                                'original': text_input,
                                'translated': translation,
                                'timestamp': time.strftime("%H:%M:%S")
                            })
                            
                            # Display translation
                            st.success(
                                f"Original ({source_lang}): {text_input}\n"
                                f"Translated ({target_lang}): {translation}"
                            )
                            
                            # Play translation
                            st.session_state.audio_player.play_text(
                                translation,
                                languages[target_lang]
                            )
                            
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")
    
    with tab2:
        st.write("Voice Translation")
        
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.is_recording:
                if st.button("🎤 Start Recording", type="primary"):
                    st.session_state.is_recording = True
                    st.rerun()
            else:
                if st.button("⏹️ Stop Recording", type="primary"):
                    st.session_state.is_recording = False
                    st.rerun()
        
        if st.session_state.is_recording:
            try:
                status_placeholder = st.empty()
                recognizer = initialize_recognizer()
                
                with sr.Microphone() as source:
                    status_placeholder.info("🎤 Listening... Speak now")
                    text = recognize_speech(recognizer, source)
                    
                    if text:
                        status_placeholder.info("🔄 Translating...")
                        src_code = languages[source_lang]
                        dest_code = languages[target_lang]
                        
                        translation = translate_text(
                            text,
                            src_lang=src_code,
                            dest_lang=dest_code
                        )
                        
                        if translation:
                            # Add to history
                            st.session_state.translation_history.append({
                                'original': text,
                                'translated': translation,
                                'timestamp': time.strftime("%H:%M:%S")
                            })
                            
                            # Display translation
                            st.success(
                                f"Original ({source_lang}): {text}\n"
                                f"Translated ({target_lang}): {translation}"
                            )
                            
                            # Play translation
                            st.session_state.audio_player.play_text(
                                translation,
                                languages[target_lang]
                            )
                            
                            st.session_state.is_recording = False
                            status_placeholder.empty()
                            
            except Exception as e:
                st.error(f"Voice translation error: {str(e)}")
                st.session_state.is_recording = False

    # Clear history button
    if st.button("Clear History"):
        st.session_state.translation_history = []
        st.rerun()
    
    # Display translation history
    if st.session_state.translation_history:
        st.subheader("Translation History")
        for item in reversed(st.session_state.translation_history[-5:]):
            st.text(f"[{item['timestamp']}]")
            st.info(f"Original: {item['original']}")
            st.success(f"Translated: {item['translated']}")

if __name__ == "__main__":
    main() 