# ==============================
# IMPORTS
# ==============================
import json,time
import subprocess
from google.cloud import bigquery, documentai
from google.api_core.client_options import ClientOptions

# Custom modules
from src.clients import get_bq_client, get_storage_client, credentials
from src import config

# ==============================
# CLIENT INITIALIZATION
# ==============================
# BigQuery client for running queries
bq_client = get_bq_client()

# Google Cloud Storage client for interacting with GCS buckets
storage_client = get_storage_client()


# ==============================
# BIGQUERY DATASET AND TABLE CREATION
# ==============================

def create_bq_dataset():
    """
    Create a BigQuery dataset if it doesn't exist.
    """
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
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)
    return dataset_ref


def create_audio_object_table():
    """
    Creates an external table for audio objects stored in GCS.
    Grants access to the bucket and links table to BigQuery via a connection.
    """
    table_full_name = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.AUDIO_OBJECT_TABLE_ID}"
    connection_full_name = f"projects/{config.PROJECT_ID}/locations/{config.DATASET_LOCATION}/connections/{config.CONNECTION_ID}"

    # Grant service account access to the GCS bucket
    subprocess.run([
        "gsutil", "iam", "ch",
        f"serviceAccount:{config.SERVICE_ACCOUNT_KEY_ID}:roles/storage.objectViewer",
        f"gs://{config.BUCKET_NAME}"
    ], check=True)

    # Create external table pointing to audio files in GCS
    sql = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{table_full_name}`
    WITH CONNECTION `{connection_full_name}`
    OPTIONS (
      object_metadata = 'SIMPLE',
      uris = ['gs://{config.BUCKET_NAME}/audio/*']
    );
    """
    bq_client.query(sql).result()
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)
    print(f"✅ External object table created: {table_full_name}")


def create_audio_embeddings_table():
    """
    Creates an empty table to store transcript embeddings incrementally.
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
    
    bq_client.query(create_table_query).result()
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)
    print(f"✅ Table `{table_id}` is ready!")
    

def create_course_embeddings_table():
    """
    Creates an empty table to store course/resource embeddings for recommendations.
    """
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_course_table"

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        course_id STRING,
        title STRING,
        description STRING,
        category STRING,
        url STRING
    )
    """
    
    bq_client.query(create_table_query).result()
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)
    print(f"✅ Table `{table_id}` is ready!")


# ==============================
# REMOTE MODELS
# ==============================

def create_transcription_model():
    """
    Creates a remote transcription model in BigQuery for speech-to-text.
    """
    connection_name = f"projects/{config.PROJECT_NUMBER}/locations/{config.DATASET_LOCATION.lower()}/connections/{config.CONNECTION_ID}"

    query = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_MODEL_ID}`
    REMOTE WITH CONNECTION `{connection_name}`
    OPTIONS(
        remote_service_type = 'CLOUD_AI_SPEECH_TO_TEXT_V2'
    )
    """
    bq_client.query(query).result()
    print(f"✅ Created remote transcription model {config.SPEECH_MODEL_ID}")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_gemini_remote_model():
    """
    Creates a remote Gemini model in BigQuery for generative AI tasks.
    """
    sql = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}`
    REMOTE WITH
        CONNECTION `us.{config.CONNECTION_ID}`
        OPTIONS (ENDPOINT = '{config.GENERATIVE_AI_MODEL_ENDPOINT}');
    """
    bq_client.query(sql).result()
    print(f"✅ Remote Gemini model `{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}` created.")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_text_embedding_model():
    """
    Creates a remote BigQuery model pointing to a Vertex AI embedding endpoint.
    """
    model_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}"
    
    query = f"""
    CREATE OR REPLACE MODEL `{model_id}`
    REMOTE WITH CONNECTION `us.{config.CONNECTION_ID}`
    OPTIONS(ENDPOINT='{config.GENERATIVE_AI_EMBEDDING_MODEL_ENDPOINT}');
    """
    bq_client.query(query).result()
    print(f"✅ Remote embedding model created: {model_id}")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


# ==============================
# DOCUMENT INGESTION
# ==============================

def create_layout_parser_processor():
    """
    Creates a Layout Parser Processor in Document AI.
    Returns processor_id for use in remote models.
    """
    location = config.DATASET_LOCATION
    processor_display_name = "layout_parser_processor"
    processor_type = "LAYOUT_PARSER_PROCESSOR"

    opts = ClientOptions(api_endpoint="us-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(
        credentials=credentials, 
        client_options=opts
    )

    parent = client.common_location_path(config.PROJECT_ID, location.lower())
    processor = client.create_processor(
        parent=parent,
        processor=documentai.Processor(
            display_name=processor_display_name,
            type_=processor_type
        ),
    )

    print(f"✅ Document AI processor created: {processor.name}")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)
    processor_id = processor.name.split("/")[-1]
    return processor_id


def create_external_pdf_table():
    """
    Creates an external table in BigQuery pointing to PDFs in GCS.
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
    print("✅ External PDF object table created.")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_remote_parser_model(processor_id: str):
    """
    Creates a remote Document AI model in BigQuery referencing the Layout Parser processor.
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
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_parsed_table():
    """
    Creates a parsed PDF table with defined schema.
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
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_speech_doc_embeddings_table():
    """
    Creates the embeddings table for processed documents if it doesn't exist.
    """
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}"
    try:
        bq_client.get_table(table_id)
        print(f"✅ Embeddings table already exists: {table_id}")
    except:
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
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def create_vector_index_if_not_exists():
    """
    Creates a vector index on the embeddings table for similarity search.
    """
    sql = f"""
    CREATE OR REPLACE VECTOR INDEX my_index 
    ON `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}`(text_embeddings)
    OPTIONS(index_type = 'TREE_AH', distance_type = 'COSINE')
    """
    bq_client.query(sql).result()
    print("✅ Vector index created (or replaced).")
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)


def insert_courses(file_path="data/courses/courses.json"):
    """
    Reads courses from a JSON file, inserts them into BigQuery,
    and generates embeddings while creating a new table to avoid streaming buffer issues.
    """

    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_course_table"
    embedding_model = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}"

    # 1️⃣ Read the courses.json file
    with open(file_path, "r") as f:
        courses = json.load(f)

    # 2️⃣ Prepare rows
    rows_to_insert = []
    for course in courses:
        rows_to_insert.append({
            "course_id": course.get("course_id"),
            "title": course.get("title"),
            "description": course.get("description"),
            "category": course.get("category"),
            "url": course.get("url")
        })

    # 3️⃣ Insert courses into BigQuery table
    errors = bq_client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print("❌ Errors occurred while inserting:", errors)
        return
    else:
        print(f"✅ Inserted {len(rows_to_insert)} courses")

    # 4️⃣ Create a new table with embeddings (avoid streaming buffer issue)
    embedding_table = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.COURSE_TABLE_ID}"

    query = f"""
    CREATE OR REPLACE TABLE `{embedding_table}` AS
    SELECT c.*,emb.ml_generate_embedding_result AS course_embedding
    FROM `{table_id}` AS c
    JOIN ML.GENERATE_EMBEDDING(
        MODEL `{embedding_model}`,
        (SELECT course_id, CONCAT(title, " ", description, " Category: ", category) AS content
         FROM `{table_id}`),
        STRUCT(TRUE AS flatten_json_output)
    ) AS emb
    USING(course_id)
    """

    # 5️⃣ Run the query
    bq_client.query(query).result()
    print(f"✅ Created table `{embedding_table}` with embeddings")
    
    print("⏳ Waiting 5 seconds to reflect")
    time.sleep(5)

    # 6️⃣ Delete the original table
    bq_client.delete_table(table_id, not_found_ok=True)




def create_document_ingestion_setup():
    """
    Run all document ingestion setup steps.
    """
    processor_id = create_layout_parser_processor()
    create_external_pdf_table()
    create_remote_parser_model(processor_id)
    create_speech_doc_embeddings_table()


# ==============================
# RESOURCE CREATION
# ==============================
def create_resources():
    """
    Run all initial setup and resource creation steps.
    """
    create_bq_dataset()
    create_transcription_model()
    create_gemini_remote_model()
    create_text_embedding_model()
    create_audio_object_table()
    create_audio_embeddings_table()
    create_course_embeddings_table()
    create_document_ingestion_setup()
    pass

def ingest_data():
    insert_courses()

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    create_resources()
    ingest_data()
    # delete_resources()  # Optional: implement deletion if needed