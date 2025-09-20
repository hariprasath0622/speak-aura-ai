# ==============================================
# src/bigquery_utils/transcription.py
# ==============================================
# Transcribe audio stored in GCS using BigQuery ML Speech-to-Text model
# and store results back in BigQuery.
# ==============================================

import json,os
from google.cloud import bigquery
from datetime import datetime
from zoneinfo import ZoneInfo
from src import config
from google import genai

# Absolute path to credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
    os.path.join(os.path.dirname(__file__), f"../{config.SERVICE_ACCOUNT_KEY_FILE_PATH}")
)

def transcribe_audio(gcs_uri: str, bq_client: bigquery.Client):
    """
    Transcribe audio stored in GCS using BigQuery ML.TRANSCRIBE.
    
    Args:
        gcs_uri (str): Full GCS path to the audio file.
        bq_client (bigquery.Client): Initialized BigQuery client.

    Returns:
        tuple:
            (True, transcripts: pd.DataFrame) on success
            (False, message: str) on failure
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
    
    # ⛔ Early exit if no transcripts
    if transcripts.empty or "transcripts" not in transcripts.columns:
        if "ml_transcribe_status" in transcripts.columns and not transcripts["ml_transcribe_status"].empty:
            error_detail = transcripts["ml_transcribe_status"].iloc[0]  # first value
        else:
            error_detail = "Unknown error"

        msg = f"❌ No transcript generated for {gcs_uri}. Because {error_detail}. Exiting pipeline."
        return False, msg

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
    load_job.result()
    print("✅ Transcription complete and stored in BigQuery!")

    return True, transcripts


def fetch_ai_sample_texts(category: str) -> list:
    """
    Generate multiple AI-generated sample texts for a given category using Gemini 2.5 Flash.

    Args:
        category (str): Category of the sample text
        n_samples (int): Number of samples to generate (default 10)

    Returns:
        List[str]: List of generated sample texts
    """

    # Initialize the client (make sure you have set GOOGLE_APPLICATION_CREDENTIALS)
    client = genai.Client(vertexai=True,project=config.PROJECT_ID, location="global")

    max_tokens = config.category_max_tokens.get(category, 150)

    prompt_text = f"Generate a clear and concise script in the category '{category}'. The text should be suitable for reading aloud, focused only on the required content, and free of unnecessary details."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
        config={
        "temperature": 0.5,  
        "maxOutputTokens": max_tokens 
        }
    )

    # Extract generated text from response
    return response.text