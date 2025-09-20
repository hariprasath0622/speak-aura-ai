# ==============================
# Streamlit tab: Speech Therapy Docs
# ==============================
# Allows users to upload PDFs or read from a local folder,
# process them with Document AI, and store results in BigQuery.

import os
from src import config
from src.bigquery_utils.pdf_processing import process_pdf_in_bigquery, get_processed_files
from src.upload_to_gcs import upload_document

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st, bq_client):
    """
    Render the "Speech Therapy Docs" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
        bq_client: BigQuery client instance
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("📂 Speech Therapy Docs")
        st.write(
            "Upload PDFs or choose files from your computer → process with Document AI → store securely in BigQuery and "
            "ask the AI therapy chat for personalized insights with your data or general guidance on speech therapy."
        )

        # -----------------------------
        # Source Selection
        # -----------------------------
        option = st.radio(
            "Choose source:",
            ["📤 Upload PDF", "📁 Read from Local Folder"],
            horizontal=True
        )

        # -----------------------------
        # Upload Single PDF
        # -----------------------------
        if option == "📤 Upload PDF":
            uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
            
            if uploaded_file is not None:
                processed_files = get_processed_files(st, bq_client)
                gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{uploaded_file.name}"

                if gcs_uri in processed_files:
                    st.info(f"✅ {uploaded_file.name} already processed. Skipping.")
                else:
                    st.info(f"📤 {uploaded_file.name} ready to upload. Click 'Submit' to start processing.")
                    
                    # Submit button to start upload & processing
                    if st.button("Submit"):
                        progress_text = st.empty()
                        progress_bar = st.progress(0)

                        # Step 1: Upload
                        progress_text.text(f"📤 Uploading {uploaded_file.name}...")
                        gcs_uri = upload_document(uploaded_file, uploaded_file.name)
                        progress_bar.progress(10)
                        progress_text.text(f"✅ Uploaded {uploaded_file.name} to GCS")

                        # Step 2: Process
                        progress_text.text(f"🔍 Processing {uploaded_file.name} with Document AI")
                        process_pdf_in_bigquery(bq_client, gcs_uri, progress_bar, progress_text)
                        progress_bar.progress(100)
                        progress_text.text(f"✅ {uploaded_file.name} parsed and stored in BigQuery!")


        # -----------------------------
        # Load PDFs from Local Folder
        # -----------------------------
        elif option == "📁 Read from Local Folder":
            folder_path = st.text_input("Enter local folder path", "./pdfs")
            if st.button("📂 Load PDFs"):
                processed_files = get_processed_files(st, bq_client)

                if os.path.exists(folder_path):
                    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

                    if pdf_files:
                        st.write(f"Found {len(pdf_files)} PDF(s):")
                        progress_text = st.empty()
                        progress_bar = st.progress(0)

                        for idx, pdf in enumerate(pdf_files):
                            gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{pdf}"

                            if gcs_uri in processed_files:
                                st.info(f"✅ {pdf} already processed. Skipping.")
                                continue

                            # Step 1: Upload
                            progress_text.text(f"📤 Uploading {pdf}...")
                            local_path = os.path.join(folder_path, pdf)
                            with open(local_path, "rb") as f:
                                gcs_uri = upload_document(f, pdf)
                            progress_bar.progress(10)
                            progress_text.text(f"✅ Uploaded {pdf} to GCS")

                            # Step 2: Process
                            progress_text.text(f"🔍 Processing {uploaded_file.name} with Document AI")
                            process_pdf_in_bigquery(bq_client, gcs_uri, progress_bar, progress_text)
                            progress_bar.progress(100)
                            progress_text.text(f"✅ {pdf} parsed and stored in BigQuery!")

                            # Update overall progress
                            progress_bar.progress((idx + 1) / len(pdf_files) * 100)

                    else:
                        st.warning("No PDF files found in the folder.")
                else:
                    st.error("Folder path does not exist.")
