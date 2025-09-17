# ==============================================
# src/bigquery_utils/transcription.py
# ==============================================
# Transcribe audio stored in GCS using BigQuery ML Speech-to-Text model
# and store results back in BigQuery.
# ==============================================

import json
from google.cloud import bigquery
from datetime import datetime
from zoneinfo import ZoneInfo
from src import config

def transcribe_audio(gcs_uri: str, bq_client: bigquery.Client):
    """
    Transcribe audio stored in GCS using BigQuery ML.TRANSCRIBE.
    
    Args:
        gcs_uri (str): Full GCS path to the audio file.
        bq_client (bigquery.Client): Initialized BigQuery client.

    Returns:
        pd.DataFrame: Transcription results with timestamps.
    """

    print(f"▶️ Starting transcription for: {gcs_uri}")

    # Recognition config for ML.TRANSCRIBE
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

    # Write results back to BigQuery
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