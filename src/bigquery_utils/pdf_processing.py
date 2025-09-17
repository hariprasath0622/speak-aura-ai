# ==============================
# src/bigquery_utils/pdf_processing.py
# ==============================
# Functions for processing PDF documents via Document AI,
# generating embeddings, and storing results in BigQuery.
# Also tracks which PDFs have already been processed.

import uuid
from src import config

# -----------------------------
# Process PDF and Generate Embeddings
# -----------------------------
def process_pdf_in_bigquery(bq_client, gcs_uri):
    """
    Processes a PDF with Document AI, generates embeddings, and appends
    both parsed content and embeddings to the final embeddings table.

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client.
        gcs_uri (str): GCS URI of the PDF file to process.

    Workflow:
        1. Create a temporary table using ML.PROCESS_DOCUMENT.
        2. Parse the JSON results into another temporary table.
        3. Generate embeddings using ML.GENERATE_EMBEDDING.
        4. Append embeddings to the main embeddings table.
        5. Clean up temporary tables.
    """
    # Generate unique temporary table names per PDF
    temp_process_table = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_process_{uuid.uuid4().hex[:8]}"
    temp_parsed_table = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_parsed_{uuid.uuid4().hex[:8]}"

    # 1️⃣ Process document into temp table
    process_options = '{"layout_config": {"chunking_config": {"chunk_size": 200}}}'
    process_query = f"""
    CREATE OR REPLACE TABLE `{temp_process_table}` AS
    SELECT * FROM ML.PROCESS_DOCUMENT(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.LAYOUT_PARSER_REMOTE_MODEL}`,
        TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.PDF_DATA_OBJECT_TABLE_ID}`,
        PROCESS_OPTIONS => (JSON '{process_options}')
    )
    WHERE uri = '{gcs_uri}'
    """
    bq_client.query(process_query).result()

    # 2️⃣ Parse JSON results into another temp table
    parse_query = f"""
    CREATE OR REPLACE TABLE `{temp_parsed_table}` AS
    SELECT
        uri,
        JSON_EXTRACT_SCALAR(json, '$.chunkId') AS chunk_id,
        JSON_EXTRACT_SCALAR(json, '$.content') AS content,
        CAST(JSON_EXTRACT_SCALAR(json, '$.pageSpan.pageStart') AS INT64) AS page_start,
        CAST(JSON_EXTRACT_SCALAR(json, '$.pageSpan.pageEnd') AS INT64) AS page_end
    FROM `{temp_process_table}`,
    UNNEST(JSON_EXTRACT_ARRAY(ml_process_document_result.chunkedDocument.chunks, '$')) AS json
    """
    bq_client.query(parse_query).result()

    # 3️⃣ Generate embeddings and append to main embeddings table
    embed_query = f"""
    INSERT INTO `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}` 
    SELECT
        uri,
        chunk_id,
        content,
        page_start,
        page_end,
        ml_generate_embedding_result AS embedding
    FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
        TABLE `{temp_parsed_table}`,
        STRUCT(TRUE AS flatten_json_output, 'RETRIEVAL_DOCUMENT' AS task_type)
    )
    """
    bq_client.query(embed_query).result()

    # 4️⃣ Cleanup temporary tables
    bq_client.query(f"DROP TABLE IF EXISTS `{temp_process_table}`").result()
    bq_client.query(f"DROP TABLE IF EXISTS `{temp_parsed_table}`").result()

# -----------------------------
# Fetch Already Processed PDFs
# -----------------------------
def get_processed_files(st, bq_client):
    """
    Retrieve a set of URIs for PDFs already processed and stored in
    the embeddings table.

    Args:
        st (streamlit): Streamlit object for displaying warnings.
        bq_client (bigquery.Client): Initialized BigQuery client.

    Returns:
        set: Set of GCS URIs already processed.
    """
    query = f"""
        SELECT DISTINCT uri
        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}`
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return set(df['uri'].tolist())
    except Exception as e:
        st.warning(f"Could not fetch processed files: {e}")
        return set()
