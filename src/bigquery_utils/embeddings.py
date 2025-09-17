# ==============================
# src/bigquery_utils/embeddings.py
# ==============================
# Functions for generating transcript embeddings and performing
# semantic search on past cases using BigQuery ML and VECTOR_SEARCH.

from google.cloud import bigquery
from src import config
import pandas as pd

# -----------------------------
# Generate Transcript Embeddings
# -----------------------------
def generate_transcript_embedding(bq_client, transcript_text):
    """
    Generate a vector embedding for a transcript using a remote BigQuery ML model.

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client.
        transcript_text (str): Transcript text to embed.

    Returns:
        list[float]: JSON-serializable embedding vector.
    """
    # Escape single quotes for SQL
    safe_transcript = transcript_text.replace("'", "\\'")

    query = f"""
    SELECT ml_generate_embedding_result AS transcript_embedding
    FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
        (SELECT '{safe_transcript}' AS content),
        STRUCT(TRUE AS flatten_json_output)
    )
    """

    # Execute query and fetch embedding
    df = bq_client.query(query).to_dataframe()
    embedding = df["transcript_embedding"].iloc[0]

    # Convert to plain Python list for JSON serialization
    return [float(x) for x in embedding]

# -----------------------------
# Fetch Similar Past Cases
# -----------------------------
def fetch_similar_cases(bq_client: bigquery.Client, embedding: list, top_k: int = 3) -> pd.DataFrame:
    """
    Perform a semantic search in BigQuery using VECTOR_SEARCH and retrieve
    top_k similar cases based on transcript embeddings.

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client.
        embedding (list): Transcript embedding to search for.
        top_k (int, optional): Number of similar cases to return. Defaults to 3.

    Returns:
        pd.DataFrame: DataFrame containing similar cases with columns:
            - run_id
            - transcript
            - metrics
            - therapy_plan
            - processed_at
            - distance
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

    # Execute query with array parameter
    job = bq_client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("embedding", "FLOAT64", embedding)
            ]
        )
    )

    # Convert result to pandas DataFrame
    similar_df = job.to_dataframe()
    return similar_df