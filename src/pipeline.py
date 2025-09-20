# ==============================
# src/pipeline.py
# ==============================
# End-to-end pipeline for SpeakAura AI:
#   1. Upload audio to GCS
#   2. Transcribe audio via BigQuery AI
#   3. Analyze stammer patterns and generate embeddings
# Uses Streamlit for progress updates.

import os
from src.upload_to_gcs import upload_audio
from src.bigquery_utils.transcription import transcribe_audio
from src.analyze_stammer import analyze_stammer
from src.clients import get_bq_client

# -----------------------------
# Suppress gRPC verbosity in logs
# -----------------------------
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"

# -----------------------------
# Initialize BigQuery client
# -----------------------------
bq_client = get_bq_client()

# -----------------------------
# Pipeline Function
# -----------------------------
def run_pipeline(local_file, st):
    """
    End-to-end pipeline for processing a single audio file.
    Performs upload, transcription, and stammer analysis while updating
    progress in the Streamlit UI.

    Args:
        local_file (str): Local path to audio file (.wav or .mp3)
        st (module): Streamlit module for UI updates
        bq_client (bigquery.Client): BigQuery client

    Returns:
        tuple: (analysis dict | None, transcript embedding | None)
    """
    # Define steps for progress display
    steps = [
        "Uploading audio to cloud storage",
        "Transcribing audio using ML.TRANSCRIBE()",
        "Analyzing stammer patterns",
        "Generating Therapy Plans",
        "Choosing AI-Recommended Courses Based on Your Speech Analysis",
        "Creating Gamified Exercises Just for You"
    ]

    # Initialize Streamlit progress bar and status text
    progress_bar = st.progress(0)
    status_text = st.empty()

    # -----------------------------
    # Step 1: Upload audio to GCS
    # -----------------------------
    status_text.text(f"📤 {steps[0]}...")
    gcs_path = upload_audio(local_file, f"audio/{os.path.basename(local_file)}")
    progress_bar.progress(25)

    # -----------------------------
    # Step 2: Transcribe audio
    # -----------------------------
    status_text.text(f"📝 {steps[1]}...")
    result = transcribe_audio(gcs_path, bq_client)

    if not result[0]:
        # Failure → gracefully handle
        msg = result[1]
        st.session_state["ml_transcribe_status"] = msg
        status_text.text(msg)
        st.error(msg)

        # Clear progress bar
        progress_bar.empty()

        # Ask user to upload again
        return None, None  # exit gracefully

    transcripts = result[1]
    progress_bar.progress(50)
    st.session_state["ml_transcribe_status"] = "✅ Transcription complete and stored in BigQuery"

    # -----------------------------
    # Step 3: Analyze stammer patterns
    # -----------------------------
    status_text.text(f"🔬 {steps[2]}...")
    analysis, transcript_embedding,top_courses = analyze_stammer(transcripts, bq_client,progress_bar,status_text,steps)
    progress_bar.progress(100)

    # -----------------------------
    # Pipeline complete
    # -----------------------------
    status_text.text("✅ Pipeline complete!")
    return analysis, transcript_embedding,top_courses