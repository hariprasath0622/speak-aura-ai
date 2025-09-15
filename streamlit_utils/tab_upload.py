import streamlit as st
import os
import tempfile
from datetime import datetime
from src.pipeline import run_pipeline
from data.transcripts.sample_texts import sample_texts

def render(tab, st, bq_client):
    with tab:
        st.header("Provide Your Voice Input")

        if "local_path" not in st.session_state:
            st.session_state.local_path = None

        # If already analyzed
        if st.session_state.get("current_analysis"):
            st.success("✅ Analysis complete! Visit Tab 2 for results.")
            if st.button("🔄 Record / Upload New Audio"):
                st.session_state.current_analysis = None
                st.session_state.local_path = None
                st.rerun()

        # Audio already uploaded/recorded
        elif st.session_state.local_path:
            st.audio(st.session_state.local_path, format="audio/wav")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-Record / Cancel"):
                    st.session_state.local_path = None
                    st.rerun()
            with col2:
                if st.button("✅ Use This Recording"):
                    st.success("Recording locked in. Ready for transcription.")

            if st.button("Analyze Audio"):
                with st.spinner("Running full pipeline..."):
                    analysis, transcript_embedding = run_pipeline(st.session_state.local_path)
                if analysis:
                    st.session_state.current_analysis = analysis
                    st.session_state.current_transcript_embedding = transcript_embedding
                    st.rerun()

        # No audio yet → choose input method
        else:
            input_method = st.radio("Choose input method:", ["🎤 Record Audio", "📂 Upload File"])
            if input_method == "🎤 Record Audio":
                render_record_audio(st)
            elif input_method == "📂 Upload File":
                render_upload_file(st)

def render_record_audio(st):
    st.markdown("### 📖 Sample Text to Read Aloud")
    category = st.selectbox("Choose a category:", list(sample_texts.keys()))
    if "sample_index" not in st.session_state:
        st.session_state.sample_index = 0
    if "sample_category" not in st.session_state:
        st.session_state.sample_category = category
    if category != st.session_state.sample_category:
        st.session_state.sample_category = category
        st.session_state.sample_index = 0
    current_text = sample_texts[category][st.session_state.sample_index]
    st.info(f"**Read this aloud:**\n\n{current_text}")

    if st.button("🔀 Show Another Text"):
        st.session_state.sample_index = (st.session_state.sample_index + 1) % len(sample_texts[category])
        st.rerun()

    try:
        from streamlit_mic_recorder import mic_recorder
        audio_data = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹ Stop Recording", just_once=True)
        if audio_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data["bytes"])
                st.session_state.local_path = tmp.name
            st.rerun()
    except ImportError:
        st.warning("`streamlit-mic-recorder` not installed. Run: `pip install streamlit-mic-recorder`")

def render_upload_file(st):
    audio_file = st.file_uploader("Upload a voice recording (.wav or .mp3)", type=["wav", "mp3"])
    if audio_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(audio_file.name)[1]
        filename = f"audio_{timestamp}{ext}"
        local_path = os.path.join("/tmp", filename)
        with open(local_path, "wb") as f:
            f.write(audio_file.read())
        st.session_state.local_path = local_path
        st.success(f"✅ File uploaded as `{filename}`")
        st.rerun()