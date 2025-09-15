import streamlit as st
from dotenv import load_dotenv
from src.clients import get_bq_client
from streamlit_utils import (
    tab_upload, tab_analysis, tab_semantic, tab_progress, tab_about
)

# Load environment variables
load_dotenv()

bq_client = get_bq_client()

# Initialize session state
def init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_transcript' not in st.session_state:
        st.session_state.current_transcript = None
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

def main():
    st.set_page_config(page_title="SpeakAura AI", page_icon="🎤", layout="wide")
    init_session_state()

    st.sidebar.title("SpeakAura AI 🎤")
    st.sidebar.info("AI-powered speech therapy for stammering")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎙️ Upload & Transcribe",
        "🧠 Stammer Analysis",
        "🕵️ Semantic Similarity",
        "📊 Progress Tracker",
        "ℹ️ About"
    ])

    tab_upload.render(tab1, st, bq_client)
    tab_analysis.render(tab2, st)
    tab_semantic.render(tab3, st, bq_client)
    tab_progress.render(tab4, st, bq_client)
    tab_about.render(tab5, st)

if __name__ == "__main__":
    main()