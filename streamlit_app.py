# ==============================
# IMPORTS
# ==============================
import streamlit as st
from dotenv import load_dotenv


# Custom modules
from src.clients import get_bq_client
from streamlit_utils.load_side_bar import load_side_bar
from streamlit_utils import (
    tab_courses, tab_upload, tab_analysis, tab_semantic, 
    tab_progress, tab_about, tab_ingest_document,
    tab_chat
)

# ==============================
# LOAD ENVIRONMENT VARIABLES
# ==============================
# Load .env file to access environment variables like API keys, DB credentials, etc.
load_dotenv()

# ==============================
# INITIALIZE CLIENTS
# ==============================
# Create a BigQuery client to interact with GCP
bq_client = get_bq_client()

# ==============================
# SESSION STATE INITIALIZATION
# ==============================
# Function to initialize Streamlit session state variables
def init_session_state():
    # Store conversation history
    if 'history' not in st.session_state:
        st.session_state.history = []

    # Store the current transcript of uploaded audio
    if 'current_transcript' not in st.session_state:
        st.session_state.current_transcript = None

    # Store the current analysis results
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

    if "current_top_courses" not in st.session_state:
        st.session_state.current_analysis = None


# ==============================
# MAIN APP FUNCTION
# ==============================
def main():
    # Set page configuration
    st.set_page_config(
        page_title="SpeakAura AI", 
        page_icon="🎤", 
        layout="wide"
    )

    # Initialize session state
    init_session_state()
    
    
    # ==============================
    # SIDEBAR
    # ==============================
    # st.sidebar.title("SpeakAura AI")
    # st.sidebar.info("AI-powered speech therapy for stammering")
    
    load_side_bar(st)

    
    # ==============================
    # TABS
    # ==============================
    # Define the different sections of the app
    tab1, tab2, tab3, tab4, tab5, tab6, tab7,tab8 = st.tabs([
        "🎙️ Upload & Transcribe",      # Upload audio and get transcript
        "🧠 Stammer Insights",         # Analyze speech patterns and provide insights
        "🎓 Recommended Courses & Crafted Exercises",
        "📊 Progress Dashboard",       # Track therapy progress over time
        "🕵️ Similar Cases",            # Compare transcripts or detect similarity
        "📂 Knowledge Base",           # Store and retrieve reference documents
        "💬 AI Therapy Chat",          # Chat with AI for therapy guidance
        "ℹ️ About Us"                 # App info, instructions, credits
    ])

    # ==============================
    # RENDER TABS
    # ==============================
    tab_upload.render(tab1, st, bq_client)
    tab_analysis.render(tab2, st)
    tab_courses.render(tab3)   # <-- NEW
    tab_progress.render(tab4, st, bq_client)
    tab_semantic.render(tab5, st, bq_client)
    tab_ingest_document.render(tab6, st, bq_client)
    tab_chat.render(tab7, st, bq_client)
    tab_about.render(tab8, st)

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    main()