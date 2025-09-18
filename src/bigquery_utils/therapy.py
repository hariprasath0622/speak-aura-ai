# ==============================
# src/analyze_stammer.py
# ==============================
# Function to generate personalized therapy plans based on transcript
# and speech metrics using BigQuery Generative AI.
# ==============================

import json
from src import config
import pandas as pd

def generate_therapy_plan(transcript_text: str, metrics_dict: dict, bq_client):
    """
    Generate a personalized speech therapy plan using BigQuery Generative AI.

    Args:
        transcript_text (str): Transcribed speech of the user.
        metrics_dict (dict): Dictionary containing speech metrics
                             (e.g., severity_score, filler_count, repetitions, long_pauses).
        bq_client: Initialized BigQuery client.

    Returns:
        str: Generated therapy plan.
    """

    # Convert metrics dict to JSON, ensuring any DataFrame is serializable
    metrics_dict_serializable = metrics_dict.copy()
    for key, value in metrics_dict_serializable.items():
        if isinstance(value, pd.DataFrame):
            metrics_dict_serializable[key] = value.to_dict(orient="records")

    metrics_json = json.dumps(metrics_dict_serializable)

    # Build AI prompt with guidance
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
              and recommend only light practice (like reading aloud daily for 5 min). 
              Keep response short, clear, and motivating.
        - Otherwise:
            → Give a concise therapy plan with:
                - Key focus areas
                - 4-5 practical exercises
                - Suggested frequency (daily/weekly)
                - Motivating tone
        - Avoid overwhelming or boring text; use bullet points if needed.
    """

    # Escape for safe insertion into SQL
    therapy_prompt_safe = therapy_prompt.replace("'", "\\'").replace("\n", "\\n")

    # BigQuery AI GENERATE call
    sql = f"""
    SELECT AI.GENERATE(
        ('{therapy_prompt_safe}', ''),
        connection_id => 'us.{config.CONNECTION_ID}',
        endpoint => '{config.GENERATIVE_AI_MODEL_ENDPOINT}',
        output_schema => 'therapy_plan STRING'
    ).therapy_plan AS therapy_plan
    """

    # Execute query and fetch result
    query_job = bq_client.query(sql)
    result_df = query_job.result().to_dataframe()
    
    if result_df.empty:
        return "No therapy plan generated."
    
    return result_df['therapy_plan'].iloc[0]