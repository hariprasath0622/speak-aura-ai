# streamlit_utils/tab_about.py

import streamlit as st

def render(tab, st):
    with tab:
        st.header("ℹ️ About SpeakAura AI")
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
        - Run multimodal analysis  

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

        ---
        **Learn More About Stammering / Stuttering:**  
        - [Stuttering Foundation](https://www.stutteringhelp.org/)  
        - [STAMMA Research](https://stamma.org/features/how-many-adults-stammer)
        """)