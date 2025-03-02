import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
from io import BytesIO
import time
import base64
import sounddevice as sd
import numpy as np
import wave
import io

def autoplay_audio(audio_bytes):
    """Autoplay audio in streamlit"""
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

def text_to_speech(text, lang):
    """Convert text to speech"""
    try:
        audio_bytes = BytesIO()
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes.read()
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

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

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone"""
    try:
        st.write("🎤 Recording...")
        audio_data = sd.rec(int(duration * sample_rate),
                          samplerate=sample_rate,
                          channels=1,
                          dtype='int16')
        sd.wait()
        return audio_data.flatten()
    except Exception as e:
        st.error(f"Recording error: {str(e)}")
        return None

def save_audio_data(audio_data, sample_rate=16000):
    """Convert numpy array to WAV file bytes"""
    try:
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        return byte_io
    except Exception as e:
        st.error(f"Audio conversion error: {str(e)}")
        return None

def live_translation(source_lang, target_lang, languages):
    """Handle live voice translation"""
    try:
        # Record audio
        audio_data = record_audio()
        if audio_data is None:
            return
            
        # Convert to WAV format
        audio_bytes = save_audio_data(audio_data)
        if audio_bytes is None:
            return
            
        # Convert speech to text
        recognizer = sr.Recognizer()
        audio_bytes.seek(0)
        with sr.AudioFile(audio_bytes) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language=languages[source_lang])
            
            if text:
                st.info(f"Recognized: {text}")
                
                # Translate text
                translation = translate_text(
                    text,
                    src_lang=languages[source_lang],
                    dest_lang=languages[target_lang]
                )
                
                if translation:
                    st.success(f"Translation: {translation}")
                    
                    # Convert to speech
                    audio_bytes = text_to_speech(translation, languages[target_lang])
                    if audio_bytes:
                        st.audio(audio_bytes, format='audio/mp3')
                        autoplay_audio(audio_bytes)
                        
                    # Add to history
                    st.session_state.translation_history.append({
                        'original': text,
                        'translated': translation,
                        'timestamp': time.strftime("%H:%M:%S")
                    })
                    
    except Exception as e:
        st.error(f"Live translation error: {str(e)}")

def main():
    st.title("VerbalLink: Global Voice Bridge")
    st.markdown("##### Interactive Multilingual Conversation Companion")
    
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
    
    language_category = st.radio(
        "Language Category",
        ["All Languages", "Indian Languages Only"],
        horizontal=True
    )
    
    indian_languages = {k: v for k, v in languages.items() if v in 
                       ['hi', 'bn', 'te', 'mr', 'ta', 'ur', 'gu', 'kn', 'ml', 'pa', 'as', 'sa', 'ne']}
    
    display_languages = languages if language_category == "All Languages" else indian_languages
    
    # Add tabs for different input methods
    tab1, tab2 = st.tabs(["Text Translation", "Voice Translation"])
    
    with tab1:
        source_lang = st.selectbox("Select source language:", list(display_languages.keys()), key="text_source")
        target_lang = st.selectbox("Select target language:", list(display_languages.keys()), key="text_target")
        
        text_input = st.text_area("Enter text to translate:", key="text_input")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            translate_button = st.button("Translate Text", key="text_translate")
        with col2:
            speak_button = st.button("🔊 Speak Translation", key="speak_translation")
        
        if translate_button and text_input:
            try:
                src_code = languages[source_lang]
                dest_code = languages[target_lang]
                
                translation = translate_text(
                    text_input,
                    src_lang=src_code,
                    dest_lang=dest_code
                )
                
                if translation:
                    st.session_state.last_translation = translation
                    st.session_state.last_lang_code = dest_code
                    
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
                    
            except Exception as e:
                st.error(f"Translation error: {str(e)}")
        
        if speak_button and 'last_translation' in st.session_state:
            audio_bytes = text_to_speech(
                st.session_state.last_translation,
                st.session_state.last_lang_code
            )
            if audio_bytes:
                autoplay_audio(audio_bytes)
    
    with tab2:
        st.write("Voice Translation")
        source_lang = st.selectbox("Select source language:", list(display_languages.keys()), key="voice_source")
        target_lang = st.selectbox("Select target language:", list(display_languages.keys()), key="voice_target")
        
        # Add tabs for different voice input methods
        voice_tab1, voice_tab2 = st.tabs(["Live Recording", "File Upload"])
        
        with voice_tab1:
            st.write("Speak directly into your microphone")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if st.button("🎤 Start Recording", key="start_recording"):
                    live_translation(source_lang, target_lang, languages)
            
            with col2:
                st.info("Click the button and speak for 5 seconds")
        
        with voice_tab2:
            # File uploader for audio
            audio_file = st.file_uploader("Upload audio file", type=['wav', 'mp3'])
            
            if audio_file:
                try:
                    # Convert audio to text
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_file) as source:
                        audio = recognizer.record(source)
                        text = recognizer.recognize_google(audio, language=languages[source_lang])
                        
                    if text:
                        # Translate
                        translation = translate_text(
                            text,
                            src_lang=languages[source_lang],
                            dest_lang=languages[target_lang]
                        )
                        
                        if translation:
                            st.success(
                                f"Original ({source_lang}): {text}\n"
                                f"Translated ({target_lang}): {translation}"
                            )
                            
                            # Convert translation to speech
                            audio_bytes = text_to_speech(translation, languages[target_lang])
                            if audio_bytes:
                                st.audio(audio_bytes, format='audio/mp3')
                                
                except Exception as e:
                    st.error(f"Voice translation error: {str(e)}")

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