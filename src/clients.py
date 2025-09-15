# src/bq_client.py
from google.cloud import bigquery, storage
from google.oauth2 import service_account
from google.cloud.speech_v2 import SpeechClient
import os
from google.cloud import bigquery_connection_v1
from google.cloud import speech_v2

# Path to your service account key
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials", "bhack-471114-2b12cc8d7377.json")

# Create credentials and client
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

def get_bq_client():
    bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    return bq_client

def get_storage_client():
    storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
    return storage_client

def get_speech_client():
    speech_client = SpeechClient(credentials=credentials)
    return speech_client

def get_bq_connection_v1_client():
    return bigquery_connection_v1.ConnectionServiceClient(credentials=credentials)