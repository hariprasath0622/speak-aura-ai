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

def load_side_bar(st):
    logo_base64 = get_img_as_base64("assets/logo.png")
    # Sidebar logo and tagline
    # Sidebar logo
    st.sidebar.markdown(
    f"""
    <div class="sidebar-logo" style="
    margin-top: -13px;
    margin-left: 28px;
    border-radius: 12px;
    box-shadow: rgba(75, 209, 192, 0.4) 0px 1px 6px;
    display: inline-block;"
    >
        <img src="{logo_base64}" style="
            width: 150px; 
            height:auto; 
            object-fit: contain; 
            border-radius: 12px;" />
    </div>
    """,
    unsafe_allow_html=True
    )

    st.sidebar.markdown(
        '<div class="sidebar-tagline" style="margin: 9%;">✨ AI-powered speech therapy for stammering ✨</div>',
        unsafe_allow_html=True
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
        
        </style>
        """,
        unsafe_allow_html=True
    )