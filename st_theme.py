import streamlit as st
import base64

# ==============================
# UTILS
# ==============================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_img_as_base64(path):
    return f"data:image/png;base64,{get_base64_of_bin_file(path)}"

# ==============================
# MODULAR TAB FUNCTIONS
# ==============================
def render_upload(st):
    st.subheader("🎙️ Upload & Transcribe")
    st.markdown('<div class="stCard">Upload audio or record voice for transcription.</div>', unsafe_allow_html=True)

def render_analysis(st):
    st.subheader("🧠 Stammer Insights")
    st.markdown('<div class="stCard">Speech pattern analysis results will appear here.</div>', unsafe_allow_html=True)

def render_semantic(st):
    st.subheader("🕵️ Similarity Check")
    st.markdown('<div class="stCard">Compare transcripts or check similarity.</div>', unsafe_allow_html=True)

def render_progress(st):
    st.subheader("📊 Progress Dashboard")
    st.markdown('<div class="stCard">Track your therapy progress over time.</div>', unsafe_allow_html=True)

def render_knowledge(st):
    st.subheader("📂 Knowledge Base")
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.write(
        "Explore reference documents, FAQs, and curated resources to support your therapy journey."
    )
    st.markdown("- 📄 Therapy guides and documents")
    st.markdown("- 🔍 Searchable FAQs")
    st.markdown("- 📚 Educational videos and articles")
    st.markdown("</div>", unsafe_allow_html=True)

def render_chat(st):
    st.subheader("💬 AI Therapy Chat")
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.write(
        "Use the chat interface below to communicate with the AI therapist, ask questions, and get personalized guidance."
    )
    user_input = st.text_area("Your message:", height=80)
    if st.button("Send"):
        st.info(f"Message sent: {user_input}")
    st.markdown("</div>", unsafe_allow_html=True)

def render_about(st):
    st.subheader("ℹ️ About App")
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.write(
        """
        SpeakAura AI is an AI-powered speech therapy tool designed specifically 
        to assist individuals with stammering. This app enables audio upload, 
        detailed speech analysis, and interactive AI therapy chat.
        
        **Credits:**
        - Developed by SpeakAura Team
        - Powered by Google Cloud and AI services
        
        **Instructions:**
        Use the sidebar to navigate through different features. 
        For questions or feedback, use the AI Therapy Chat section.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# MAIN APP FUNCTION
# ==============================
def main():
    st.set_page_config(
        page_title="SpeakAura AI",
        page_icon="🎤",
        layout="wide"
    )

    # Load sidebar background image
    sidebar_bg = get_img_as_base64("assets/side_bar_bg_1.png")

    # Inject custom CSS
    st.markdown(
        f"""
        <style>
        /* Card styling */
        .stCard {{
            background: #23272A;
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.18);
            margin-bottom: 16px;
        }}

        /* Sidebar background */
        [data-testid="stSidebar"] {{
            background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)),
                        url("{sidebar_bg}") !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            color: white !important;
        }}

        /* Sidebar text */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {{
            color: white !important;
        }}

        /* Custom tagline box */
        .sidebar-tagline {{
            background: rgba(0,0,0,0.55);
            color: #ffffff;
            text-align: center;
            font-size: 14px;
            padding: 10px;
            border-radius: 10px;
            margin: 8px 0 20px 0;
        }}

        /* Better spacing for radio options */
        [role=radiogroup] > label {{
            margin-bottom: 12px !important;
            display: flex;
            align-items: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    logo_base64 = get_img_as_base64("assets/logo.png")
    # Sidebar logo and tagline
    # Sidebar logo
    st.sidebar.markdown(
        f"""
        <div style="
            text-align:center; 
            margin-top:-50px; 
            padding: 0px 0; 
            border-radius: 12px; 
            box-shadow: 0 0 15px rgba(79, 209, 197, 0.4);
            background: transparent;">
            <img src="{logo_base64}" style="width: 150px; height:auto; object-fit: contain; margin-bottom:5px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        '<div class="sidebar-tagline">✨ AI-powered speech therapy for stammering ✨</div>',
        unsafe_allow_html=True
    )

    # Sidebar navigation
    section = st.sidebar.radio(
        "Navigation",
        [
            "🎙️ Upload & Transcribe",
            "🧠 Stammer Insights",
            "🕵️ Similarity Check",
            "📊 Progress Dashboard",
            "📂 Knowledge Base",
            "💬 AI Therapy Chat",
            "ℹ️ About App",
        ]
    )

    # Render selected page
    if section == "🎙️ Upload & Transcribe":
        render_upload(st)
    elif section == "🧠 Stammer Insights":
        render_analysis(st)
    elif section == "🕵️ Similarity Check":
        render_semantic(st)
    elif section == "📊 Progress Dashboard":
        render_progress(st)
    elif section == "📂 Knowledge Base":
        render_knowledge(st)
    elif section == "💬 AI Therapy Chat":
        render_chat(st)
    elif section == "ℹ️ About App":
        render_about(st)


# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    main()