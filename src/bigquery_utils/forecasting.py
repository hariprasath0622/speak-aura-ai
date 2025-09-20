# ==============================
# src/bigquery_utils/forecasting.py
# ==============================
# Functions for fetching user progress data and generating forecasts
# using BigQuery ML / AI.FORECAST.

from src import config
import pandas as pd

# -----------------------------
# Fetch Historical Progress Data
# -----------------------------
def fetch_progress_data(bq_client):
    """
    Retrieve user progress data from BigQuery, including stammer analysis metrics
    and the timestamps when each transcript was processed.

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client.

    Returns:
        pd.DataFrame: DataFrame with columns:
            - run_id
            - metrics (JSON string)
            - processed_at (timestamp)
    """
    query = f"""
    SELECT run_id, metrics, processed_at
    FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`
    ORDER BY processed_at ASC
    """
    query_job = bq_client.query(query)
    results_df = query_job.to_dataframe()
    return results_df

# -----------------------------
# Fetch Forecasted Progress (Daily Aggregation)
# -----------------------------

def fetch_forecast(bq_client, horizon: int = 10, confidence_level: float = 0.8) -> pd.DataFrame:
    """
    Generate forecasted fluency scores using BigQuery AI.FORECAST.
    Only real forecast values are returned (no synthetic fallback).

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client.
        horizon (int): Number of future points to forecast.
        confidence_level (float): Confidence interval level (between 0 and 1).

    Returns:
        pd.DataFrame: Forecasted data with columns:
            - forecast_timestamp
            - fluency_forecast
            - prediction_interval_lower_bound
            - prediction_interval_upper_bound
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
            DATE(processed_at) AS processed_day,
            AVG(
              COALESCE(SAFE_CAST(JSON_VALUE(metrics, '$.severity_score') AS FLOAT64), 0) * -100 + 100
            ) AS fluency_score
          FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`
          GROUP BY processed_day
          ORDER BY processed_day
        ),
        data_col => 'fluency_score',
        timestamp_col => 'processed_day',
        horizon => {horizon},
        confidence_level => {confidence_level}
      );
    """

    forecast_df = bq_client.query(query).to_dataframe()

    return forecast_df