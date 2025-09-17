# ==============================
# src/upload_to_gcs.py
# ==============================
# Handles uploading audio and PDF files to Google Cloud Storage (GCS)
# using the configured bucket from the project settings.

import os
from src import config
from src.clients import get_storage_client

# -----------------------------
# Upload Audio Files
# -----------------------------
def upload_audio(local_file, dest_blob_name=None):
    """
    Uploads a local audio file to GCS.

    Args:
        local_file (str): Path to local audio file (.wav, .mp3)
        dest_blob_name (str, optional): Destination blob path in GCS.
            Defaults to 'audio/<filename>' if not provided.

    Returns:
        str: GCS URI of uploaded audio file
    """
    client = get_storage_client()
    bucket = client.bucket(config.BUCKET_NAME)

    # Determine destination blob name
    if not dest_blob_name:
        dest_blob_name = os.path.basename(local_file)
    else:
        # Ensure path is sanitized and prefixed with "audio/"
        filename = os.path.basename(dest_blob_name)
        dest_blob_name = f"audio/{filename}" if not dest_blob_name.startswith("audio/") else dest_blob_name

    # Upload file to GCS
    blob = bucket.blob(dest_blob_name)
    blob.upload_from_filename(local_file)

    gcs_uri = f"gs://{config.BUCKET_NAME}/{dest_blob_name}"
    print(f"✅ Uploaded to {gcs_uri}")
    return gcs_uri

# -----------------------------
# Upload PDF Documents
# -----------------------------
def upload_document(file, filename):
    """
    Uploads a PDF file to GCS under 'documents/' folder.

    Args:
        file (str or file-like): Local path or file-like object (Streamlit uploader)
        filename (str): Filename to save in GCS

    Returns:
        str: GCS URI of uploaded PDF
    """
    storage_client = get_storage_client()
    bucket = storage_client.bucket(config.BUCKET_NAME)
    blob = bucket.blob(f"documents/{filename}")

    # Upload depending on input type
    if isinstance(file, str):
        # Local path
        blob.upload_from_filename(file)
    else:
        # Streamlit uploaded file
        blob.upload_from_file(file, content_type="application/pdf")

    gcs_uri = f"gs://{config.BUCKET_NAME}/documents/{filename}"
    print(f"✅ Uploaded PDF to {gcs_uri}")
    return gcs_uri
