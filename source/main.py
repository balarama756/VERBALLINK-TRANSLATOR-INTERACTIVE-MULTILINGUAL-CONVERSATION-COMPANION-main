import streamlit as st
from deep_translator import GoogleTranslator
import time

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
    
    source_lang = st.selectbox("Select source language:", list(display_languages.keys()))
    target_lang = st.selectbox("Select target language:", list(display_languages.keys()))
    
    # Text input for translation
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