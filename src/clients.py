# ==============================
# src/client.py
# ==============================
# This file handles authentication and client creation for
# Google Cloud BigQuery and Cloud Storage using a service account.

from google.cloud import bigquery, storage
from google.oauth2 import service_account
import os
from src.config import SERVICE_ACCOUNT_KEY_FILE_PATH

# -----------------------------
# Service Account Key
# -----------------------------
# Construct full path to the service account key file
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__),
    SERVICE_ACCOUNT_KEY_FILE_PATH
)

# -----------------------------
# Create Credentials
# -----------------------------
# Initialize credentials using the service account JSON key
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# -----------------------------
# BigQuery Client
# -----------------------------
def get_bq_client():
    """
    Returns an authenticated BigQuery client using the service account credentials.

    Returns:
        bigquery.Client: Authenticated BigQuery client
    """
    bq_client = bigquery.Client(
        credentials=credentials,
        project=credentials.project_id
    )
    return bq_client

# -----------------------------
# Cloud Storage Client
# -----------------------------
def get_storage_client():
    """
    Returns an authenticated Google Cloud Storage client using the service account credentials.

    Returns:
        storage.Client: Authenticated Cloud Storage client
    """
    storage_client = storage.Client(
        credentials=credentials,
        project=credentials.project_id
    )
    return storage_client
