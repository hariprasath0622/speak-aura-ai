import pandas as pd
import json
from src import config
import uuid
from datetime import datetime
import numpy as np
from src.bigquery_utils import generate_transcript_embedding, generate_therapy_plan

def extract_word_level(transcripts_df):
    """
    Extract word-level transcripts from ml_transcribe_result JSON.

    Args:
        transcripts_df (pd.DataFrame): DataFrame containing at least columns:
            - 'ml_transcribe_result' : JSON string from transcription
            - 'uri' : GCS URI of audio file

    Returns:
        pd.DataFrame: Flattened word-level transcript with columns:
            ['uri', 'word', 'start_time', 'end_time']
    """
    all_words = []

    for _, row in transcripts_df.iterrows():
        uri = row["uri"]
        result_json = row["ml_transcribe_result"]

        if not result_json:
            continue

        try:
            data = json.loads(result_json)
            # dynamic top-level key (the GCS URI)
            top_key = list(data["results"].keys())[0]

            words_list = data["results"][top_key]["inline_result"]["transcript"]["results"][0]["alternatives"][0]["words"]

            for word_item in words_list:
                all_words.append({
                    "word": word_item["word"],
                    "start_time": float(word_item["start_offset"].replace("s","")),
                    "end_time": float(word_item["end_offset"].replace("s",""))
                })
        except Exception as e:
            print(f"Error processing {uri}: {e}")
            continue

    return pd.DataFrame(all_words)

def compute_speech_metrics(words_df):
    if words_df.empty:
        return {
            "total_words": 0,
            "filler_count": 0,
            "repetitions": 0,
            "long_pauses": 0,
            "severity_score": 0.0
        }

    # Define fillers
    # Expanded stammer/stuttering filters
    fillers = [
        # Basic fillers
        "uh", "um", "er", "ah", "hmm",
        
        # Filler with punctuation
        "uh,", "um,", "er,", "ah,",
        
        # Stuttering-style broken sounds
        "b-b-but", "c-c-can", "d-d-do", "l-l-like", "m-m-me", "s-s-so", "w-w-well"
    ]
    
    # Mark filler words
    words_df["is_filler"] = words_df["word"].str.lower().isin(fillers)
    
    # Check for immediate repetitions
    words_df["prev_word"] = words_df["word"].shift(1)
    words_df["is_repetition"] = words_df["word"] == words_df["prev_word"]

    # Calculate pauses between words
    words_df["next_start"] = words_df["start_time"].shift(-1)
    words_df["pause"] = words_df["next_start"] - words_df["end_time"]
    words_df["long_pause"] = words_df["pause"] > 1.5  # seconds

    # Metrics
    filler_count = int(words_df["is_filler"].sum())
    repetitions = int(words_df["is_repetition"].sum())
    long_pauses = int(words_df["long_pause"].sum())
    total_words = len(words_df)
    severity_score = (filler_count + repetitions + long_pauses) / total_words if total_words > 0 else 0.0

    return {
        "total_words": total_words,
        "filler_count": filler_count,
        "repetitions": repetitions,
        "long_pauses": long_pauses,
        "severity_score": severity_score
    }

def insert_analysis_result_with_embedding(bq_client, result_dict):
    """
    Insert analysis result into BigQuery with embeddings.
    """
    table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}"

    # Convert metrics and words_df to JSON
    metrics_json = json.dumps(result_dict["metrics"])
    words_df_json = (
        result_dict["words_df"].to_json(orient="records") 
        if isinstance(result_dict["words_df"], pd.DataFrame) 
        else result_dict["words_df"]
    )

    # Get embedding and convert to native Python list
    transcript_embedding = generate_transcript_embedding(bq_client, result_dict["transcript"])
    # if isinstance(transcript_embedding, np.ndarray):
    #     transcript_embedding = transcript_embedding.tolist()

    # Prepare row
    row = {
        "run_id": str(uuid.uuid4()),
        "transcript": result_dict["transcript"],
        "metrics": metrics_json,
        "therapy_plan": result_dict["therapy_plan"],
        "words_df": words_df_json,
        "transcript_embedding": transcript_embedding,  # single row, ARRAY<FLOAT64>
        "processed_at": datetime.utcnow().isoformat()
    }

    errors = bq_client.insert_rows_json(table_id, [row])
    if errors:
        print(f"❌ Insert failed: {errors}")
    else:
        print(f"✅ Inserted result with embedding into {table_id} (run_id={row['run_id']})")
        return transcript_embedding

# Updated analyze_stammer function
def analyze_stammer(transcripts_df, bq_client):
    if transcripts_df.empty:
        return None
    
    transcript_text = transcripts_df["transcripts"].iloc[0]
    words_df = extract_word_level(transcripts_df)
    # print("Word-level breakdown:\n", words_df.head())
    
    metrics = compute_speech_metrics(words_df)
    # print("Speech metrics:\n", metrics)
    
    therapy_plan = generate_therapy_plan(transcript_text, metrics, bq_client)
    
    result = {
        "transcript": transcript_text,
        "metrics": metrics,
        "therapy_plan": therapy_plan,
        "words_df": words_df
    }

    # Insert into single table with embeddings
    transcript_embedding = insert_analysis_result_with_embedding(bq_client, result)

    return result, transcript_embedding
