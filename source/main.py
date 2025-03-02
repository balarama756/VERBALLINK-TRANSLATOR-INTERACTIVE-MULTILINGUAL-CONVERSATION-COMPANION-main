import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
from googletrans import Translator
import time
import sounddevice as sd
import soundfile as sf
from io import BytesIO

class AudioPlayer:
    def __init__(self):
        self.sample_rate = 24000

    def play_text(self, text, lang='en'):
        try:
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to temporary file
            temp_file = f"temp_{time.time()}.wav"
            tts.save(temp_file)
            
            # Read and play the audio
            data, samplerate = sf.read(temp_file)
            sd.play(data, samplerate)
            sd.wait()  # Wait until audio is finished playing
            
            # Cleanup
            os.remove(temp_file)
            
        except Exception as e:
            st.error(f"Text-to-speech error: {e}")

    def __del__(self):
        try:
            sd.stop()
        except:
            pass

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
    """Enhanced translation with better error handling and retries"""
    if not text:
        return None
        
    for attempt in range(retries):
        try:
            # Create a new translator instance for each attempt
            translator = Translator(service_urls=[
                'translate.google.com',
                'translate.google.co.in',
                'translate.google.co.uk'
            ])
            
            # Add a small delay between retries
            if attempt > 0:
                time.sleep(1)
            
            # Perform translation
            translation = translator.translate(
                text=text,
                src=src_lang,
                dest=dest_lang
            )
            
            if translation and translation.text:
                return translation.text
                
        except Exception as e:
            st.error(f"Translation attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                return None
            continue
            
    return None

def check_audio_device():
    """Check if audio input device is available"""
    try:
        with sr.Microphone() as source:
            return True
    except OSError:
        return False

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
        text_input = st.text_area("Enter text to translate:", key="text_input")
        
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
                        handle_translation(text_input, translation, source_lang, target_lang, languages)
                        
                except Exception as e:
                    st.error(f"Translation error: {str(e)}")
    
    with tab2:
        st.write("Voice Translation")
        
        # Check for microphone availability first
        try:
            # Test microphone access
            with sr.Microphone() as source:
                pass
            
            # Only show recording controls if microphone is available
            if 'is_recording' not in st.session_state:
                st.session_state.is_recording = False
            
            # Single button for start/stop recording
            if not st.session_state.is_recording:
                if st.button("Start Conversation", type="primary", key="start_recording"):
                    st.session_state.is_recording = True
                    st.rerun()
            else:
                if st.button("Stop Conversation", type="primary", key="stop_recording"):
                    st.session_state.is_recording = False
                    st.rerun()
            
            # Show recording status and handle recording
            if st.session_state.is_recording:
                status_placeholder = st.empty()
                status_placeholder.info("🎤 Listening... (Click 'Stop Conversation' when done)")
                
                try:
                    recognizer = initialize_recognizer()
                    with sr.Microphone() as source:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        status_placeholder.info("Processing speech...")
                        
                        text = recognizer.recognize_google(audio)
                        if text:
                            status_placeholder.info("Translating...")
                            src_code = languages[source_lang]
                            dest_code = languages[target_lang]
                            
                            translation = translate_text(
                                text,
                                src_lang=src_code,
                                dest_lang=dest_code
                            )
                            
                            if translation:
                                handle_translation(text, translation, source_lang, target_lang, languages)
                                
                except sr.UnknownValueError:
                    status_placeholder.warning("Could not understand audio. Please try again.")
                except sr.RequestError:
                    status_placeholder.error("Could not request results. Check your internet connection.")
                except Exception as e:
                    status_placeholder.error(f"Error during recording: {str(e)}")
                    
        except OSError:
            # Show friendly message if no microphone is available
            st.error("❌ No microphone detected")
            st.info("💡 Please use the Text Input tab instead")
            st.session_state.is_recording = False
        except Exception as e:
            st.error(f"Error initializing microphone: {str(e)}")
            st.info("💡 Please use the Text Input tab instead")
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

def handle_translation(original_text, translation, source_lang, target_lang, languages):
    """Helper function to handle translation results"""
    # Add to history
    st.session_state.translation_history.append({
        'original': original_text,
        'translated': translation,
        'timestamp': time.strftime("%H:%M:%S")
    })
    
    # Display translation
    st.success(
        f"Original ({source_lang}): {original_text}\n"
        f"Translated ({target_lang}): {translation}"
    )
    
    # Speak translation
    st.session_state.audio_player.play_text(
        translation,
        languages[target_lang]
    )

if __name__ == "__main__":
    main() 