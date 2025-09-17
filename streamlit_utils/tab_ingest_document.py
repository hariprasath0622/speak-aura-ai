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
        st.write("Upload PDFs or load from a local folder → process with Document AI → store in BigQuery")

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
                # Get list of already processed files
                processed_files = get_processed_files(st, bq_client)
                gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{uploaded_file.name}"

                if gcs_uri in processed_files:
                    st.info(f"✅ {uploaded_file.name} already processed. Skipping.")
                else:
                    # Upload file to GCS
                    st.info(f"Uploading {uploaded_file.name} to GCS...")
                    gcs_uri = upload_document(uploaded_file, uploaded_file.name)
                    st.success(f"✅ Uploaded to {gcs_uri}")

                    # Process with Document AI in BigQuery
                    st.info("Processing with Document AI in BigQuery...")
                    process_pdf_in_bigquery(bq_client, gcs_uri)
                    st.success("✅ PDF parsed and stored in BigQuery!")

        # -----------------------------
        # Load PDFs from Local Folder
        # -----------------------------
        elif option == "📁 Read from Local Folder":
            folder_path = st.text_input("Enter local folder path", "./pdfs")
            if st.button("📂 Load PDFs"):
                processed_files = get_processed_files(st, bq_client)

                if os.path.exists(folder_path):
                    # Find all PDF files in folder
                    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

                    if pdf_files:
                        st.write(f"Found {len(pdf_files)} PDF(s):")

                        # Loop through PDFs and upload/process each
                        for pdf in pdf_files:
                            gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{pdf}"

                            if gcs_uri in processed_files:
                                st.info(f"✅ {pdf} already processed. Skipping.")
                                continue

                            # Upload file to GCS
                            st.write(f"📤 Uploading {pdf}...")
                            local_path = os.path.join(folder_path, pdf)
                            with open(local_path, "rb") as f:
                                gcs_uri = upload_document(f, pdf)

                            st.success(f"✅ Uploaded {pdf} to {gcs_uri}")

                            # Process PDF with Document AI in BigQuery
                            st.info(f"Processing {pdf} with Document AI...")
                            process_pdf_in_bigquery(bq_client, gcs_uri)
                            st.success(f"✅ {pdf} parsed and stored in BigQuery!")

                    else:
                        st.warning("No PDF files found in the folder.")
                else:
                    st.error("Folder path does not exist.")
