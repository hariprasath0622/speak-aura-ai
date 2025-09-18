import pandas as pd
import json
import uuid
from datetime import datetime
from src import config
from src.bigquery_utils.embeddings import generate_transcript_embedding
from src.bigquery_utils.therapy import generate_therapy_plan

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

            results = data["results"][top_key]["inline_result"]["transcript"].get("results", [])

            for result in results:
                alternatives = result.get("alternatives", [])
                if not alternatives:
                    continue

                words_list = alternatives[0].get("words", [])
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


def compute_speech_metrics(words_df, long_pause_thresh=1.5):
    """
    Advanced stammer/stuttering analysis for word-level transcripts.

    Args:
        words_df (pd.DataFrame): Word-level transcript with columns ['word', 'start_time', 'end_time']
        long_pause_thresh (float): Threshold for long pauses in seconds

    Returns:
        dict: Summary metrics
        pd.DataFrame: Word-level analysis with disfluency annotations
    """
    if words_df.empty:
        return {}, pd.DataFrame()

    df = words_df.copy()
    
    # --- Disfluency detection ---
    fillers = ["uh", "um", "ah", "er", "hmm"]
    df["is_filler"] = df["word"].str.lower().str.strip(",.")\
                        .isin(fillers)
    
    # Immediate word repetitions
    df["prev_word"] = df["word"].shift(1)
    df["is_repetition"] = df["word"] == df["prev_word"]

    # Prolongations: repeated letters (>2)
    df["is_prolongation"] = df["word"].str.match(r"([a-zA-Z])\1{2,}", case=False)

    # Inter-word pauses
    df["next_start"] = df["start_time"].shift(-1)
    df["pause"] = df["next_start"] - df["end_time"]
    df["is_block"] = df["pause"] > long_pause_thresh

    # --- Speech metrics ---
    total_words = len(df)
    total_duration = df["end_time"].max() - df["start_time"].min()
    speech_rate = total_words / total_duration if total_duration > 0 else 0

    filler_count = int(df["is_filler"].sum())
    repetitions = int(df["is_repetition"].sum())
    prolongations = int(df["is_prolongation"].sum())
    blocks = int(df["is_block"].sum())
    long_pause_count = blocks  # same as blocks

    # Weighted severity score
    # Assign weights: block=3, prolongation=2, repetition=1.5, filler=1
    severity_score = (
        3*blocks + 2*prolongations + 1.5*repetitions + 1*filler_count
    ) / total_words

    # Severity level
    if severity_score < 0.1:
        severity_level = "Mild"
    elif severity_score < 0.25:
        severity_level = "Moderate"
    else:
        severity_level = "Severe"

    summary = {
        "total_words": total_words,
        "total_duration_sec": total_duration,
        "speech_rate_wps": speech_rate,
        "filler_count": filler_count,
        "repetitions": repetitions,
        "prolongations": prolongations,
        "blocks": blocks,
        "long_pauses": long_pause_count,
        "severity_score": severity_score,
        "severity_level": severity_level
    }

    # Keep only useful columns for word-level analysis
    df = df[["word", "start_time", "end_time", "pause", 
             "is_filler", "is_repetition", "is_prolongation", "is_block"]]

    return summary, df


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
    
    metrics, words_analysis = compute_speech_metrics(words_df)
    # print("Speech metrics:\n", metrics)
    
    therapy_plan = generate_therapy_plan(transcript_text, metrics, bq_client)
    
    result = {
        "transcript": transcript_text,
        "metrics": metrics,
        "therapy_plan": therapy_plan,
        "words_df": words_analysis
    }

    # Insert into single table with embeddings
    transcript_embedding = insert_analysis_result_with_embedding(bq_client, result)

    return result, transcript_embedding
