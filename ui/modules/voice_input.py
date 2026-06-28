import tempfile
import streamlit as st
from transformers import pipeline
from streamlit_mic_recorder import mic_recorder

@st.cache_resource
def load_asr():
    return pipeline(
        task="automatic-speech-recognition",
        model="openai/whisper-base",
        device=-1
    )

def process_audio():
    audio = mic_recorder(
        start_prompt="🎙️ Записать",
        stop_prompt="⏹️ Остановить",
        key="rec",
        args=(),
        kwargs={}
    )
    return audio

def get_asr_result(asr, audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    
    result = asr(tmp_path)
    return result["text"].strip()

def clear_text():
    st.session_state.text_input_3 = ""
    st.session_state.voice_input = ""
    st.session_state._last_asr_result = ""
    st.session_state._last_audio_sig = None
    st.session_state._clear_audio_after = True

def append_text(new_text: str):
    new_text = new_text.strip()
    if not new_text:
        return

    current = st.session_state.text_input_3.strip()
    updated = f"{current} {new_text}".strip() if current else new_text

    st.session_state.text_input_3 = updated
    st.session_state.voice_input = updated
    st.session_state._last_asr_result = updated
