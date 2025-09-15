import os
from src import config
from src.clients import get_storage_client


def upload_to_gcs(local_file, dest_blob_name=None):
    client = get_storage_client()
    bucket = client.bucket(config.BUCKET_NAME)

    # If dest_blob_name not provided → use just the filename
    if not dest_blob_name:
        dest_blob_name = os.path.basename(local_file)
    else:
        # Always sanitize to avoid accidental /tmp paths
        filename = os.path.basename(dest_blob_name)
        dest_blob_name = f"audio/{filename}" if not dest_blob_name.startswith("audio/") else dest_blob_name

    blob = bucket.blob(dest_blob_name)
    blob.upload_from_filename(local_file)

    gcs_uri = f"gs://{config.BUCKET_NAME}/{dest_blob_name}"
    print(f"✅ Uploaded to {gcs_uri}")
    return gcs_uri