# ==============================
# streamlit_utils/tab_about.py
# ==============================
# This file defines the "About" tab in the Streamlit UI for SpeakAura AI.
# It provides an overview of the app, its problem-solution approach,
# practical impact, and technical workings using BigQuery AI.

import streamlit as st

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st):
    """
    Render the "About SpeakAura AI" tab in Streamlit.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("ℹ️ About SpeakAura AI")

        # -----------------------------
        # Markdown Content
        # -----------------------------
        st.markdown("""
        **SpeakAura AI** — an end-to-end BigQuery AI pipeline that detects stammering 
        and generates personalized therapy plans.  

        **Problem:** 70M+ people worldwide stammer. They face communication anxiety, 
        stigma, and limited therapy access.  

        **Solution:** SpeakAura AI uses **BigQuery AI** + **Generative AI** to:
        - Transcribe voice input  
        - Detect stammering patterns  
        - Track & forecast progress  
        - Find semantic similarities (**Semantic Detective**)  
        - Ingest Speech Documents & Chat with AI Speech Therapist 

        ---
        ### 🌍 Practical Impact – How It Helps People
        - 🗣️ Provides **accessible speech therapy support** anytime, anywhere  
        - 💰 **Affordable alternative** to in-person sessions  
        - ⏱️ Enables **early intervention** by detecting stammering patterns quickly  
        - 📈 Helps users **track progress over time** with clear metrics  
        - 🔍 **Finds similar past cases** using semantic embeddings to suggest therapy insights  
        - ❤️ Reduces **anxiety & stigma** by offering private, AI-powered practice

        ---
        ### 🔧 How It Works with BigQuery AI
        - 🎤 **Audio ingested into BigQuery** via **GCS connection**  
        - 📝 **Speech-to-text transcription** performed using **Vertex AI Speech + BigQuery ML**  
        - 🔍 **Transcript processed & flattened** into word-level data for detailed analysis  
        - 📊 **Stammer metrics detected** (fillers, repetitions, pauses) using **SQL + Python**  
        - 🧠 **Therapy plan generated** using **`AI.GENERATE`** (Gemini model) based on transcript + metrics  
        - 🔄 **Semantic Detective finds similar cases**:
            1. Generate transcript embeddings using **`ML.GENERATE_EMBEDDINGS`**  
            2. Perform top-k vector search using **`VECTOR_SEARCH`**  
        - 📈 **Results stored back in BigQuery** for continuous tracking & progress monitoring
        - 📄 **Speech therapy documents ingested**:
            - PDF contents are converted to embeddings and a vector index is created
            - Enables AI to provide domain-specific answers and generate therapy plans

        ---
        **Learn More About Stammering / Stuttering:**  
        - [Stuttering Foundation](https://www.stutteringhelp.org/)  
        - [STAMMA Research](https://stamma.org/features/how-many-adults-stammer)
        """)