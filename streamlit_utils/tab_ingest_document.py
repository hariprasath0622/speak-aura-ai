import os
from src import config
from src.bigquery_utils import process_pdf_in_bigquery,get_processed_files
from src.upload_to_gcs import upload_document 

def render(tab, st,bq_client):
    with tab:
        st.header("📂 SPEECH Therapy Document Manager")
        st.write("Upload PDFs or load from a local folder → process with Document AI → store in BigQuery")

        option = st.radio(
            "Choose source:",
            ["📤 Upload PDF", "📁 Read from Local Folder"],
            horizontal=True
        )

        processed_files = get_processed_files(st,bq_client)

        if option == "📤 Upload PDF":
            uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
            if uploaded_file is not None:
                gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{uploaded_file.name}"
                if gcs_uri in processed_files:
                    st.info(f"✅ {uploaded_file.name} already processed. Skipping.")
                else:
                    st.info(f"Uploading {uploaded_file.name} to GCS...")
                    gcs_uri = upload_document (uploaded_file, uploaded_file.name)
                    st.success(f"✅ Uploaded to {gcs_uri}")

                    st.info("Processing with Document AI in BigQuery...")
                    process_pdf_in_bigquery(bq_client, gcs_uri)
                    st.success("✅ PDF parsed and stored in BigQuery!")

        elif option == "📁 Read from Local Folder":
            folder_path = st.text_input("Enter local folder path", "./pdfs")

            if st.button("📂 Load PDFs"):
                if os.path.exists(folder_path):
                    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
                    if pdf_files:
                        st.write(f"Found {len(pdf_files)} PDF(s):")

                        for pdf in pdf_files:
                            gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{pdf}"
                            if gcs_uri in processed_files:
                                st.info(f"✅ {pdf} already processed. Skipping.")
                                continue

                            st.write(f"📤 Uploading {pdf}...")
                            local_path = os.path.join(folder_path, pdf)
                            with open(local_path, "rb") as f:
                                gcs_uri = upload_document(f, pdf)

                            st.success(f"✅ Uploaded {pdf} to {gcs_uri}")
                            st.info(f"Processing {pdf} with Document AI...")
                            process_pdf_in_bigquery(bq_client, gcs_uri)
                            st.success(f"✅ {pdf} parsed and stored in BigQuery!")
                    else:
                        st.warning("No PDF files found in the folder.")
                else:
                    st.error("Folder path does not exist.")