import os
from google.cloud import bigquery
from clients import get_bq_client, get_storage_client,credentials
import subprocess
import config

from google.cloud import bigquery, documentai
from google.api_core.client_options import ClientOptions
# -----------------------------
# Clients
# -----------------------------
bq_client = get_bq_client()
storage_client = get_storage_client()


# -----------------------------
# Functions
# -----------------------------

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



# ---------------- DOCUMENT INGESTION FUNCTIONS ---------------- #

# ---------------- DOCUMENT AI PROCESSOR ---------------- #
def create_layout_parser_processor():
    """
    Creates a Layout Parser Processor in Document AI and returns processor_id.
    One-time setup.
    """
    location = config.DATASET_LOCATION  # e.g., "us"
    processor_display_name = "layout_parser_processor"
    processor_type = "LAYOUT_PARSER_PROCESSOR"

    opts = ClientOptions(api_endpoint="us-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(credentials=credentials,client_options=opts)

    parent = client.common_location_path(config.PROJECT_ID, location.lower())
    processor = client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            display_name=processor_display_name,
            type_=processor_type
        ),
    )

    # Print the processor information
    print(f"✅ Document AI processor created:")
    print(f"Processor Name: {processor.name}")
    print(f"Processor Display Name: {processor.display_name}")
    print(f"Processor Type: {processor.type_}")

    processor_id = processor.name.split("/")[-1]
    return processor_id

# ---------------- EXTERNAL OBJECT TABLE ---------------- #
def create_external_pdf_table():
    """
    Creates an external object table pointing to PDFs in GCS.
    One-time setup.
    """
    sql = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.PDF_DATA_OBJECT_TABLE_ID}`
    WITH CONNECTION `{config.DATASET_LOCATION}.{config.CONNECTION_ID}`
    OPTIONS (
      uris = ['gs://{config.BUCKET_NAME}/documents/*'],
      object_metadata = 'DIRECTORY'
    )
    """
    bq_client.query(sql).result()
    print("✅ External object table created.")


# ---------------- REMOTE DOCUMENT AI MODEL ---------------- #
def create_remote_parser_model(processor_id: str):
    """
    Creates a remote Document AI model in BigQuery referencing the Layout Parser processor.
    One-time setup.
    """
    sql = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.LAYOUT_PARSER_REMOTE_MODEL}`
    REMOTE WITH CONNECTION `{config.DATASET_LOCATION}.{config.CONNECTION_ID}`
    OPTIONS (
        remote_service_type="CLOUD_AI_DOCUMENT_V1",
        document_processor="{processor_id}"
    )
    """
    bq_client.query(sql).result()
    print("✅ Remote parser model created.")


# ---------------- PARSED TABLE ---------------- #
def create_parsed_table():
    """
    Creates parsed PDF table with proper schema.
    One-time setup.
    """
    schema = [
        bigquery.SchemaField("uri", "STRING"),
        bigquery.SchemaField("chunk_id", "STRING"),
        bigquery.SchemaField("content", "STRING"),
        bigquery.SchemaField("page_footers_text", "STRING"),
        bigquery.SchemaField("page_start", "INT64"),
        bigquery.SchemaField("page_end", "INT64"),
    ]
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.PARSED_PDF_TABLE_ID}"
    table = bigquery.Table(table_id, schema=schema)
    table = bq_client.create_table(table, exists_ok=True)
    print(f"✅ Parsed table created: {table_id}")


def create_embeddings_table_if_not_exists():
    """
    Creates the embeddings table if it doesn't exist.
    Should be run once before processing PDFs incrementally.
    """
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}"

    # Create table if it doesn't exist
    try:
        bq_client.get_table(table_id)
        print(f"✅ Embeddings table already exists: {table_id}")
    except:
        # Define a minimal schema (columns will match ML.GENERATE_EMBEDDING output)
        schema = [
            bigquery.SchemaField("uri", "STRING"),
            bigquery.SchemaField("chunk_id", "STRING"),
            bigquery.SchemaField("content", "STRING"),
            bigquery.SchemaField("page_start", "INT64"),
            bigquery.SchemaField("page_end", "INT64"),
            bigquery.SchemaField("text_embeddings", "FLOAT64", mode="REPEATED"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        bq_client.create_table(table)
        print(f"✅ Embeddings table created: {table_id}")

def create_vector_index_if_not_exists():

    sql = f"""CREATE OR REPLACE VECTOR INDEX my_index ON `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}`(text_embeddings) 
    OPTIONS(index_type = 'TREE_AH',
    distance_type = 'COSINE')
    """

    bq_client.query(sql).result()
    print("✅ Vector index created (or replaced).")


def create_document_ingestion_setup():
    """Run all one-time setup steps."""
    processor_id = create_layout_parser_processor()
    create_external_pdf_table()
    create_remote_parser_model(processor_id)
    create_embeddings_table_if_not_exists()

# -----------------------------
# Resource Creation
# -----------------------------

def create_resources():
    # create_bq_dataset()
    # create_transcription_model()
    # create_gemini_remote_model()
    # create_text_embedding_model()
    # create_audio_object_table()
    create_embeddings_table()
    # create_document_ingestion_setup()
    pass

# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":
    create_resources()
    # delete_resources()