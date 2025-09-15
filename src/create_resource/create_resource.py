import os
from google.cloud import bigquery
from clients import get_bq_client, get_storage_client
import subprocess
import config

# -----------------------------
# Clients
# -----------------------------
bq_client = get_bq_client()
storage_client = get_storage_client()


# -----------------------------
# Functions
# -----------------------------
def create_gcs_bucket():
    bucket_name = config.BUCKET_NAME
    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        storage_client.create_bucket(bucket, location=config.DATASET_LOCATION)
        print(f"✅ Created bucket {bucket_name}")
    else:
        print(f"ℹ️ Bucket {bucket_name} already exists")
    return bucket


def create_bq_dataset():
    dataset_ref = bigquery.Dataset(f"{config.PROJECT_ID}.{config.DATASET_ID}")
    dataset_ref.location = config.DATASET_LOCATION
    try:
        bq_client.create_dataset(dataset_ref)
        print(f"✅ Created dataset {config.DATASET_ID} in {config.DATASET_LOCATION}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️ Dataset {config.DATASET_ID} already exists")
        else:
            raise
    return dataset_ref


def create_audio_object_table():
    client = bq_client
    table_full_name = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.AUDIO_OBJECT_TABLE_ID}"
    connection_full_name = f"projects/{config.PROJECT_ID}/locations/{config.DATASET_LOCATION}/connections/{config.CONNECTION_ID}"

    # Grant access to the GCS bucket
    subprocess.run([
        "gsutil", "iam", "ch",
        f"serviceAccount:{config.SERVICE_ACCOUNT_KEY_ID}:roles/storage.objectViewer",
        f"gs://{config.BUCKET_NAME}"
    ], check=True)

    # Create external table
    sql = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{table_full_name}`
    WITH CONNECTION `{connection_full_name}`
    OPTIONS (
      object_metadata = 'SIMPLE',
      uris = ['gs://{config.BUCKET_NAME}/audio/*']
    );
    """
    client.query(sql).result()
    print(f"External object table created: {table_full_name}")


def create_analysis_results_table():
    """Create analysis_results table with transcript, metrics, therapy plan, and words_df JSON."""
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULT_TABLE_ID}"
    
    sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        run_id STRING,                 -- unique id per run
        transcript STRING,
        metrics JSON,                  -- metrics dict as JSON
        therapy_plan STRING,
        words_df JSON,                 -- full word-level breakdown stored as JSON
        processed_at TIMESTAMP
    )
    """
    job = bq_client.query(sql)
    job.result()
    print(f"✅ Table ready: {table_id}")

def create_embeddings_table():
    """
    Creates an empty table for storing transcript embeddings incrementally.
    """
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}"

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        run_id STRING,
        transcript STRING,
        metrics JSON,
        therapy_plan STRING,
        words_df JSON,
        processed_at TIMESTAMP,
        transcript_embedding ARRAY<FLOAT64>
    )
    """
    
    query_job = bq_client.query(create_table_query)
    query_job.result() 
    print(f"✅ Table `{table_id}` is ready!")

def create_transcription_model():
    connection_name = f"projects/{config.PROJECT_NUMBER}/locations/{config.DATASET_LOCATION.lower()}/connections/{config.CONNECTION_ID}"

    query = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_MODEL_ID}`
    REMOTE WITH CONNECTION `{connection_name}`
    OPTIONS(
        remote_service_type = 'CLOUD_AI_SPEECH_TO_TEXT_V2'
    )
    """
    bq_client.query(query).result()
    print(f"✅ Created remote transcription model {config.SPEECH_MODEL_ID} in dataset {config.DATASET_ID}")

def create_gemini_remote_model():
    """
    Create or replace a remote Gemini model in BigQuery.

    Args:
        project_id (str): GCP project ID.
        dataset_id (str): BigQuery dataset where the model will be created.
        model_id (str): Name of the model to create.
        connection_id (str): BigQuery Connection ID pointing to Vertex AI.
        endpoint (str): Gemini model endpoint, e.g., 'gemini-2.5-flash'.
    """

    sql = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}`
    REMOTE WITH
        CONNECTION `us.{config.CONNECTION_ID}`
        OPTIONS (ENDPOINT = '{config.GENERATIVE_AI_MODEL_ENDPOINT}');
    """

    query_job = bq_client.query(sql)
    query_job.result()  # Wait for the job to complete
    print(f"Remote Gemini model `{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}` created successfully.")

def create_text_embedding_model():
    """
    Creates or replaces a remote BigQuery model pointing to a Vertex AI embedding endpoint.
    """
    model_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}"
    
    query = f"""
    CREATE OR REPLACE MODEL `{model_id}`
    REMOTE WITH CONNECTION `us.{config.CONNECTION_ID}`
    OPTIONS(ENDPOINT='{config.GENERATIVE_AI_EMBEDDING_MODEL_ENDPOINT}');
    """
    
    query_job = bq_client.query(query)
    query_job.result()  # Wait for the job to complete
    print(f"✅ Remote embedding model created: {model_id}")

# -----------------------------
# Resource Creation
# -----------------------------

def create_resources():
    # create_gcs_bucket()
    # create_bq_dataset()
    # create_transcription_model()
    # create_gemini_remote_model()
    # create_text_embedding_model()
    # create_audio_object_table()
    # create_analysis_results_table()
    # create_embeddings_table()
    pass

# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":
    create_resources()
    # delete_resources()