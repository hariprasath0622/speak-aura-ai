import os
from src.upload_to_gcs import upload_audio
from src.bigquery_utils import transcribe_audio
from src.analyze_stammer import analyze_stammer
from src.clients import get_bq_client

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_LOG_SEVERITY_LEVEL"] = "ERROR"

bq_client = get_bq_client()



def run_pipeline(local_file):
    """
    End-to-end pipeline: upload, transcribe, analyze stammer.
    Assumes the audio object table already exists in BigQuery.
    """
    # Upload to GCS
    gcs_path = upload_audio(local_file, f"audio/{os.path.basename(local_file)}")

    # Transcribe
    transcripts = transcribe_audio(gcs_path,bq_client)

    # Analyze stammer
    analysis,transcript_embedding = analyze_stammer(transcripts,bq_client)

    return analysis,transcript_embedding