import json
from google.cloud import bigquery
from datetime import datetime
from zoneinfo import ZoneInfo
from src import config
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def transcribe_audio(gcs_uri, bq_client):
    """
    Runs BigQuery ML.TRANSCRIBE on the uploaded audio file.
    """
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
    transcripts = bq_client.query(query).to_dataframe()

    # BigQuery returns UTC → add IST column
    utc_now = datetime.now(ZoneInfo("UTC"))
    ist_now = utc_now.astimezone(ZoneInfo("Asia/Kolkata"))

    transcripts["processed_at"] = utc_now  # keep UTC TIMESTAMP
    transcripts["processed_at_ist"] = ist_now.replace(tzinfo=None)  # store as DATETIME (no tz)

    # Save transcripts to BigQuery
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.TRANSCRIBE_TABLE_ID}"
    bq_client.load_table_from_dataframe(
                    dataframe=transcripts,
                    destination=table_id,
                    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    ).result()

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

    query = """
    SELECT run_id, metrics, processed_at
    FROM `bhack-471114.speakaura_ai_dataset.analysis_results_embeddings`
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
          FROM `bhack-471114.speakaura_ai_dataset.analysis_results_embeddings`
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


