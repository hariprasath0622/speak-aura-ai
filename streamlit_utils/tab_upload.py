# ==============================
# streamlit_utils/tab_upload.py
# ==============================
# This file defines the "Upload & Record Audio" tab in Streamlit.
# Users can record or upload voice input for stammer analysis.
# Integrates with the full AI pipeline for transcription and embeddings.

import streamlit as st
import os
import tempfile
from datetime import datetime
from src.pipeline import run_pipeline
from data.transcripts.sample_texts import sample_texts
from src.bigquery_utils.transcription import fetch_ai_sample_texts

# ==============================
# MAIN RENDER FUNCTION
# ==============================
def render(tab, st,bq_client):
    """
    Render the "Provide Your Voice Input" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("Provide Your Voice Input")

        # -----------------------------
        # Initialize session state for local audio path
        # -----------------------------
        if "local_path" not in st.session_state:
            st.session_state.local_path = None

        # -----------------------------
        # Case 1: Analysis already completed
        # -----------------------------
        if st.session_state.get("current_analysis"):
            st.success("✅ Analysis complete! Visit Tab 2 for results.")
            if st.button("🔄 Record / Upload New Audio"):
                # Reset session state to allow new recording/upload
                st.session_state.current_analysis = None
                st.session_state.local_path = None
                st.rerun()

        # -----------------------------
        # Case 2: Audio already uploaded/recorded
        # -----------------------------
        elif st.session_state.local_path:
            # Play the audio
            st.audio(st.session_state.local_path, format="audio/wav")

            # Buttons for re-recording or confirming current recording
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-Record / Cancel"):
                    st.session_state.local_path = None
                    st.rerun()
            with col2:
                if st.button("✅ Use This Recording"):
                    st.success("Recording locked in. Ready for transcription.")

            # Analyze button
            if st.button("Analyze Audio"):
                with st.spinner("Running full pipeline..."):
                    analysis, transcript_embedding,top_courses = run_pipeline(
                        st.session_state.local_path, st
                    )

                if analysis is not None:
                    # ✅ Success: save results
                    st.session_state.current_analysis = analysis
                    st.session_state.current_transcript_embedding = transcript_embedding
                    st.session_state.current_top_courses = top_courses
                    st.rerun()
                else:
                    # ❌ Failure: show retry prompt
                    st.warning("⚠️ Analysis could not be completed. Please upload a new audio file and try again.")
                    st.session_state.current_analysis = None
                    st.session_state.current_transcript_embedding = None

        # -----------------------------
        # Case 3: No audio yet → choose input method
        # -----------------------------
        else:
            input_method = st.radio("Choose input method:", ["📂 Upload File","🎤 Record Audio"])
            if input_method == "🎤 Record Audio":
                render_record_audio(st)
            elif input_method == "📂 Upload File":
                render_upload_file(st)

# ==============================
# RECORD AUDIO HELPER
# ==============================
def render_record_audio(st):
    """
    Render the UI for recording audio from microphone with sample text prompts.
    Supports static texts and AI-generated single texts.
    """
    # -----------------------------
    # Sample Text Section
    # -----------------------------
    st.markdown("### 📖 Sample Text to Read Aloud")

    # Option: Static vs AI-generated
    text_source = st.radio(
        "Choose text source:",
        options=["Static Text", "Generate with AI"]
    )

    # Categories (same for both sources)
    categories = [
        "Warm-up (short & simple)",
        "Practice Sentences",
        "Conversational",
        "Longer Reading",
        "Therapy Drills"
    ]

    if text_source == "Static Text":
        category = st.selectbox("Choose a category:", categories)
        # Initialize session state for static text
        if "sample_index" not in st.session_state:
            st.session_state.sample_index = 0
        if "sample_category" not in st.session_state:
            st.session_state.sample_category = category
        if category != st.session_state.sample_category:
            st.session_state.sample_category = category
            st.session_state.sample_index = 0

        # Fetch static sample texts
        sample_texts_list = sample_texts[category]
        current_text = sample_texts_list[st.session_state.sample_index]

        # Display current text
        st.info(f"**Read this aloud:**\n\n{current_text}")

        # Button to show another sample
        if st.button("🔀 Show Another Text"):
            st.session_state.sample_index = (st.session_state.sample_index + 1) % len(sample_texts_list)
            st.rerun()

    else:
        # AI-generated text
        category_ai = st.selectbox("Choose a category for AI generation:", categories)

        if st.button("🪄 Generate Text"):
            with st.spinner("Generating AI text..."):
                # Generate one AI sample
                ai_text = fetch_ai_sample_texts(category_ai)  # should return a string
                if ai_text:
                    st.session_state.ai_generated_text = ai_text
                else:
                    st.session_state.ai_generated_text = "Failed to generate text. Try again."

        # Display generated text if exists
        if "ai_generated_text" in st.session_state:
            st.info(f"**Read this aloud:**\n\n{st.session_state.ai_generated_text}")

    # -----------------------------
    # Audio Recording Section
    # -----------------------------
    try:
        from streamlit_mic_recorder import mic_recorder
        audio_data = mic_recorder(
            start_prompt="🎤 Start Recording",
            stop_prompt="⏹ Stop Recording",
            just_once=True
        )
        if audio_data:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data["bytes"])
                st.session_state.local_path = tmp.name
            st.rerun()
    except ImportError:
        st.warning("`streamlit-mic-recorder` not installed. Run: `pip install streamlit-mic-recorder`")

# ==============================
# UPLOAD AUDIO FILE HELPER
# ==============================
def render_upload_file(st):
    """
    Render the UI for uploading audio files (.wav or .mp3)
    """
    audio_file = st.file_uploader("Upload a voice recording (.mp3)", type=["mp3"])
    if audio_file:
        # Generate unique timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(audio_file.name)[1]
        filename = f"audio_{timestamp}{ext}"
        local_path = os.path.join("/tmp", filename)

        # Save uploaded file to local path
        with open(local_path, "wb") as f:
            f.write(audio_file.read())

        # Update session state
        st.session_state.local_path = local_path
        st.success(f"✅ File uploaded as `{filename}`")
        st.rerun()