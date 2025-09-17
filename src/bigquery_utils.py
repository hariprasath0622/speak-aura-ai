import json
from google.cloud import bigquery
from datetime import datetime
from zoneinfo import ZoneInfo
from src import config
import pandas as pd
import uuid

def transcribe_audio(gcs_uri, bq_client):
    print(f"▶️ Starting transcription for: {gcs_uri}")

    recognition_config = {
        "model": config.SPEECH_MODEL_NAME,
        "languageCodes": ["en-US"],
        "features": {
            "enableAutomaticPunctuation": True,
            "enableWordTimeOffsets": True
        },
        "autoDecodingConfig": {}
    }
    config_str = json.dumps(recognition_config).replace("'", "\\'")

    query = f"""
        SELECT *
        FROM ML.TRANSCRIBE(
            MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_MODEL_ID}`,
            (
                SELECT uri, content_type
                FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.AUDIO_OBJECT_TABLE_ID}`
                WHERE uri = '{gcs_uri}'
            ),
            RECOGNITION_CONFIG => (JSON '{config_str}')
        )
    """

    print("▶️ Running BigQuery ML.TRANSCRIBE…")
    job = bq_client.query(query)
    print(f"   Job ID: {job.job_id}")

    transcripts = job.to_dataframe()
    print(f"✅ Query finished. Rows returned: {len(transcripts)}")

    # Add timestamps
    utc_now = datetime.now(ZoneInfo("UTC"))
    ist_now = utc_now.astimezone(ZoneInfo("Asia/Kolkata"))
    transcripts["processed_at"] = utc_now
    transcripts["processed_at_ist"] = ist_now.replace(tzinfo=None)

    # Save transcripts
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.TRANSCRIBE_TABLE_ID}"
    print(f"▶️ Writing transcripts to {table_id} …")
    load_job = bq_client.load_table_from_dataframe(
        dataframe=transcripts,
        destination=table_id,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    )
    load_job.result()  # wait for completion
    print("✅ Transcription complete and stored in BigQuery!")

    return transcripts

def generate_therapy_plan(transcript_text, metrics_dict, bq_client):

    # Convert metrics dict to JSON string
    metrics_json = json.dumps(metrics_dict)

    # Build prompt
    therapy_prompt = f"""
        You are a supportive speech therapist AI assistant. 
        Analyze the transcript and metrics below to decide therapy suggestions.

        Transcript:
        {transcript_text}

        Metrics (JSON):
        {metrics_json}

        Guidelines:
        - If severity_score < 0.2 AND filler_count + repetitions + long_pauses == 0:
            → Congratulate the speaker, say their speech is clear, 
            and recommend only light practice (like reading aloud daily for 5 min) and Keep response short, clear, and motivating.
        - Otherwise:
            → Give a **concise therapy plan** with:
                - Key focus areas 
                - 4-5 practical exercises
                - Suggested frequency (daily/weekly)
                - Motivating.
        - Avoid overwhelming or boring text; use bullet points if needed.
    """

    # Escape single quotes and newlines for BigQuery SQL
    therapy_prompt_safe = therapy_prompt.replace("'", "\\'").replace("\n", "\\n")

    sql = f"""
    SELECT AI.GENERATE(
        ('{therapy_prompt_safe}', ''),
        connection_id => 'us.{config.CONNECTION_ID}',
        endpoint => '{config.GENERATIVE_AI_MODEL_ENDPOINT}',
        output_schema => 'therapy_plan STRING'
    ).therapy_plan AS therapy_plan
    """

    query_job = bq_client.query(sql)
    result_df = query_job.result().to_dataframe()
    
    if result_df.empty:
        return "No therapy plan generated."
    
    return result_df['therapy_plan'].iloc[0]

def generate_transcript_embedding(bq_client, transcript_text):
    """
    Generate vector embedding for a transcript using remote BigQuery ML model.
    Returns a plain Python list of floats (JSON-serializable).
    """
    # Escape single quotes
    safe_transcript = transcript_text.replace("'", "\\'")

    query = f"""
    SELECT ml_generate_embedding_result AS transcript_embedding
    FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
        (SELECT '{safe_transcript}' AS content),
        STRUCT(TRUE AS flatten_json_output)
    )
    """
    df = bq_client.query(query).to_dataframe()
    embedding = df["transcript_embedding"].iloc[0]

    # Convert to plain Python list of floats
    return [float(x) for x in embedding]


def fetch_similar_cases(bq_client: bigquery.Client, embedding: list, top_k: int = 3) -> pd.DataFrame:
    """
    Run a semantic search in BigQuery using VECTOR_SEARCH and return top_k similar cases.

    Args:
        bq_client (bigquery.Client): An initialized BigQuery client.
        embedding (list): Transcript embedding to search for.
        top_k (int): Number of similar cases to retrieve.

    Returns:
        pd.DataFrame: DataFrame containing similar cases.
    """
    query = f"""
    SELECT 
        base.run_id,
        base.transcript,
        base.metrics,
        base.therapy_plan,
        base.processed_at,
        distance
    FROM VECTOR_SEARCH(
        TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`,
        'transcript_embedding',
        (SELECT @embedding AS transcript_embedding),
        top_k => {top_k}
    )
    ORDER BY distance ASC;
    """

    job = bq_client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("embedding", "FLOAT64", embedding)
            ]
        )
    )

    similar_df = job.to_dataframe()
    return similar_df


def fetch_progress_data(bq_client):
    """
    Fetch user progress data (metrics + processed_at) from BigQuery.
    Returns: pandas.DataFrame
    """

    query = f"""
    SELECT run_id, metrics, processed_at
    FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`
    ORDER BY processed_at ASC
    """

    query_job = bq_client.query(query)
    results_df = query_job.to_dataframe()
    return results_df


def fetch_forecast(bq_client, horizon: int = 10, confidence_level: float = 0.8) -> pd.DataFrame:
    """
    Fetch forecasted fluency scores using AI.FORECAST from BigQuery.
    
    Args:
        bq_client: BigQuery client object
        horizon: number of future points to forecast
        confidence_level: confidence interval level (0 < level < 1)
    
    Returns:
        pd.DataFrame: forecast with columns: forecast_timestamp, fluency_forecast,
                      prediction_interval_lower_bound, prediction_interval_upper_bound
    """
    query = f"""
    SELECT
      forecast_timestamp,
      forecast_value AS fluency_forecast,
      prediction_interval_lower_bound,
      prediction_interval_upper_bound
    FROM
      AI.FORECAST(
        (
          SELECT 
            SAFE_CAST(JSON_VALUE(metrics, '$.severity_score') AS FLOAT64) * -100 + 100 AS fluency_score,
            processed_at
          FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`
          ORDER BY processed_at
        ),
        data_col => 'fluency_score',
        timestamp_col => 'processed_at',
        horizon => {horizon},
        confidence_level => {confidence_level}
      );
    """

    query_job = bq_client.query(query)
    forecast_df = query_job.to_dataframe()
    return forecast_df


def process_pdf_in_bigquery(bq_client, gcs_uri):
    """
    Processes a PDF with Document AI, generates embeddings, and appends both
    parsed content and embeddings to the final embeddings table using temporary tables.
    """

    # Generate unique temporary table names per PDF
    temp_process_table = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_process_{uuid.uuid4().hex[:8]}"
    temp_parsed_table = f"{config.PROJECT_ID}.{config.DATASET_ID}.temp_parsed_{uuid.uuid4().hex[:8]}"

    # 1️⃣ Process document using ML.PROCESS_DOCUMENT into a temp table
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

    # 3️⃣ Generate embeddings from temp parsed table and append to main embeddings table
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

    # 4️⃣ Cleanup temp tables
    bq_client.query(f"DROP TABLE IF EXISTS `{temp_process_table}`").result()
    bq_client.query(f"DROP TABLE IF EXISTS `{temp_parsed_table}`").result()

# Function to get already processed files from parsed table
def get_processed_files(st, bq_client):
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


def generate_text_with_vector_search(
    bq_client,
    user_question: str,
    top_k: int = 10,
    fraction_lists_to_search: float = 0.01,
    max_output_tokens: int = 512,
    temperature: float = 0.2,
    top_p: float = 0.9
) -> str:
    """Generate text augmented by vector search results from BigQuery using Vertex AI Gemini model."""

    options_json = json.dumps({"fraction_lists_to_search": fraction_lists_to_search})

    query = f"""
    SELECT ml_generate_text_llm_result AS generated
    FROM ML.GENERATE_TEXT(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}`,
        (
            SELECT CONCAT(
                "Question: ", @user_question, "\\n\\n",
                "Answer concisely using the context below:\\n\\n",
                STRING_AGG(
                    FORMAT("context: %s (source: %s)", base.content, base.uri),
                    "\\n\\n"
                )
            ) AS prompt
            FROM (
                SELECT uri, content, chunk_id, page_start, page_end
                FROM VECTOR_SEARCH(
                    TABLE (
                        SELECT uri, content, chunk_id, page_start, page_end, text_embeddings
                        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}`
                    ),
                    'text_embeddings',
                    (
                        SELECT ml_generate_embedding_result AS embedding
                        FROM ML.GENERATE_EMBEDDING(
                            MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
                            (SELECT @user_question AS content)
                        )
                    ),
                    top_k => @top_k,
                    OPTIONS => '{options_json}'
                )
            ) AS base
        ),
        STRUCT(
            {max_output_tokens} AS max_output_tokens,
            {temperature} AS temperature,
            {top_p} AS top_p,
            TRUE AS flatten_json_output
        )
    )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_question", "STRING", user_question),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
        ]
    )

    try:
        results = bq_client.query(query, job_config=job_config).result()
        row = next(results, None)
        return row.generated if row else "No answer generated."
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while generating the response."
