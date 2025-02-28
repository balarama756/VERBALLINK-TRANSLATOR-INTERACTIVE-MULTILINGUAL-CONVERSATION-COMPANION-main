import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
from googletrans import Translator
import time
import threading
import queue

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=44100)
        self.audio_queue = queue.Queue()
        self.play_thread = threading.Thread(target=self._play_audio_worker, daemon=True)
        self.play_thread.start()

    def _play_audio_worker(self):
        while True:
            audio_file = self.audio_queue.get()
            if audio_file is None:
                break
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()
                os.remove(audio_file)
            except Exception as e:
                st.error(f"Audio playback error: {e}")

    def play_text(self, text, lang='en'):
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            temp_file = f"temp_audio_{time.time()}.mp3"
            tts.save(temp_file)
            self.audio_queue.put(temp_file)
        except Exception as e:
            st.error(f"Text-to-speech error: {e}")

def initialize_recognizer():
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold = 300
    r.pause_threshold = 0.6
    return r

def recognize_speech(recognizer, source):
    """Enhanced speech recognition with multiple attempts"""
    try:
        # Adjust microphone for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Listen for speech with adjusted parameters
        audio = recognizer.listen(
            source,
            timeout=3,
            phrase_time_limit=5
        )
        
        # Try multiple language models for better accuracy
        for lang in ['en-IN', 'en-US', 'en-GB']:
            try:
                text = recognizer.recognize_google(audio, language=lang)
                if text and len(text.strip()) > 0:
                    return text.strip()
            except:
                continue
        
        # If specific language models fail, try auto-detection
        return recognizer.recognize_google(audio)
        
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        st.error("Could not request results from speech recognition service")
        return None
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        st.error(f"Error during speech recognition: {e}")
        return None

def translate_text(text, src_lang, dest_lang, retries=3):
    """Enhanced translation with better accuracy and error handling"""
    # List of translation services to try
    services = [
        'translate.google.com',
        'translate.google.co.in',
        'translate.google.co.uk',
        'translate.google.co.jp'
    ]
    
    # Clean and prepare the text
    text = text.strip()
    if not text:
        return None
        
    for attempt in range(retries):
        try:
            # Create a new translator for each attempt
            translator = Translator(service_urls=[services[attempt % len(services)]])
            
            # First attempt: direct translation
            translation = translator.translate(
                text,
                src=src_lang,
                dest=dest_lang
            )
            
            if translation and translation.text:
                # Verify translation quality with back-translation
                back_translation = translator.translate(
                    translation.text,
                    src=dest_lang,
                    dest=src_lang
                )
                
                # If back-translation is similar to original, return the translation
                if back_translation and back_translation.text.lower() in text.lower() or text.lower() in back_translation.text.lower():
                    return translation.text
                
                # If verification failed, try alternative translation
                alternative = translator.translate(
                    text,
                    src='auto',  # Let Google detect the source language
                    dest=dest_lang
                )
                
                if alternative and alternative.text:
                    return alternative.text
                    
            time.sleep(0.5)  # Small delay between attempts
            
        except Exception as e:
            if attempt == retries - 1:
                st.error(f"Translation failed: {str(e)}")
                return None
            time.sleep(1)  # Longer delay after error
            continue
            
    return None

def main():
    st.title("VerbalLink: Global Voice Bridge")
    
    # Add a subtitle for better context
    st.markdown("##### Interactive Multilingual Conversation Companion")
    
    if 'audio_player' not in st.session_state:
        st.session_state.audio_player = AudioPlayer()
        
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []
    
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
    
    if 'is_translating' not in st.session_state:
        st.session_state.is_translating = False
    
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.is_translating:
            if st.button("Stop Translation", type="primary"):
                st.session_state.is_translating = False
                st.rerun()
        else:
            if st.button("Start Translation", type="primary"):
                st.session_state.is_translating = True
                st.rerun()
    
    with col2:
        if st.button("Clear History"):
            st.session_state.translation_history = []
            st.rerun()
    
    if st.session_state.is_translating:
        placeholder = st.empty()
        recognizer = initialize_recognizer()
        
        with sr.Microphone() as source:
            while st.session_state.is_translating:
                placeholder.info("Listening...")
                text = recognize_speech(recognizer, source)
                
                if text:
                    try:
                        translation = translate_text(
                            text,
                            src_lang=languages[source_lang],
                            dest_lang=languages[target_lang]
                        )
                        
                        if translation:
                            # Add to history
                            st.session_state.translation_history.append({
                                'original': text,
                                'translated': translation,
                                'timestamp': time.strftime("%H:%M:%S")
                            })
                            
                            # Display latest translation
                            placeholder.success(
                                f"Original ({source_lang}): {text}\n"
                                f"Translated ({target_lang}): {translation}"
                            )
                            
                            # Speak translation
                            st.session_state.audio_player.play_text(
                                translation,
                                languages[target_lang]
                            )
                            
                    except Exception as e:
                        st.error(f"Translation error: {e}")
                        time.sleep(0.5)
                
                time.sleep(0.1)
    
    # Display translation history
    if st.session_state.translation_history:
        st.subheader("Translation History")
        for item in reversed(st.session_state.translation_history[-5:]):
            st.text(f"[{item['timestamp']}]")
            st.info(f"Original: {item['original']}")
            st.success(f"Translated: {item['translated']}")

if __name__ == "__main__":
    main() 