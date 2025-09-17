"""
Helper functions for Streamlit UI
Provides utilities for formatting transcripts, parsing stammer analysis,
tracking progress, and creating interactive charts.
"""

# ==============================
# IMPORTS
# ==============================
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# TRANSCRIPT UTILITIES
# ==============================
def format_transcript(transcript_text: str) -> str:
    """
    Clean and format the transcript text for display.
    Removes leading/trailing spaces.
    """
    return transcript_text.strip()


# ==============================
# STAMMER ANALYSIS UTILITIES
# ==============================
def parse_stammer_analysis(analysis_json: str) -> dict:
    """
    Parse JSON output from stammer analysis.
    
    Returns:
        dict: {
            'transcript': str,
            'stammer_count': int,
            'patterns': list,
            'suggestions': list
        }
    """
    try:
        data = json.loads(analysis_json)
        return {
            'transcript': data.get('transcript', ''),
            'stammer_count': data.get('analysis', {}).get('stammer_count', 0),
            'patterns': data.get('analysis', {}).get('patterns', []),
            'suggestions': data.get('analysis', {}).get('suggestions', [])
        }
    except Exception:
        return {
            'transcript': '',
            'stammer_count': 0,
            'patterns': [],
            'suggestions': []
        }


def save_session_results(transcript: str, analysis: dict) -> dict:
    """
    Save session results for progress tracking.
    
    For demo purposes, returns a dictionary.
    In production, could save to database or file.
    """
    now = datetime.now()
    return {
        'date': now.strftime('%Y-%m-%d'),
        'fluency_score': 100 - (analysis.get('stammer_count', 0) * 5),  # Example scoring
        'confidence': 75  # Placeholder: could derive from audio analysis
    }


# ==============================
# FORECAST & PROGRESS CHARTS
# ==============================
def create_forecast_chart(history_df, forecast_df) -> go.Figure:
    """
    Create a Plotly chart showing historical fluency and forecast with confidence intervals.
    """
    fig = go.Figure()

    # Historical fluency
    fig.add_trace(go.Scatter(
        x=history_df["Date"],
        y=history_df["Fluency Score"],
        mode="lines+markers",
        name="Historical Fluency",
        line=dict(color="blue")
    ))

    # Forecast fluency
    fig.add_trace(go.Scatter(
        x=forecast_df["forecast_timestamp"],
        y=forecast_df["fluency_forecast"],
        mode="lines+markers",
        name="Forecast Fluency",
        line=dict(color="green", dash="dash")
    ))

    # Confidence interval (shaded area)
    fig.add_trace(go.Scatter(
        x=list(forecast_df["forecast_timestamp"]) + list(forecast_df["forecast_timestamp"][::-1]),
        y=list(forecast_df["prediction_interval_upper_bound"]) + list(forecast_df["prediction_interval_lower_bound"][::-1]),
        fill="toself",
        fillcolor="rgba(0, 255, 0, 0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="Confidence Interval"
    ))

    fig.update_layout(
        title="Speech Progress & Forecast",
        xaxis_title="Date",
        yaxis_title="Fluency Score",
        template="plotly_white"
    )

    return fig


# ==============================
# DATAFRAME UTILITIES
# ==============================
def build_progress_df(bigquery_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert BigQuery results into a structured progress DataFrame.

    Handles missing metrics, parses JSON safely, and formats dates.
    """
    if bigquery_df.empty:
        return pd.DataFrame(columns=["Date", "Fluency Score", "Filler Count", "Repetitions", "Total Words"])

    rows = []
    for _, row in bigquery_df.iterrows():
        # Safely parse metrics JSON
        try:
            metrics = json.loads(row.get("metrics", "{}"))
        except Exception:
            metrics = {}

        severity = metrics.get("severity_score", 0)
        fluency_score = round((1 - severity) * 100, 1)

        rows.append({
            "Date": pd.to_datetime(row.get("processed_at", None)).strftime("%Y-%m-%d") if row.get("processed_at") else None,
            "Fluency Score": fluency_score,
            "Filler Count": metrics.get("filler_count", 0),
            "Repetitions": metrics.get("repetitions", 0),
            "Total Words": metrics.get("total_words", 0)
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["Date", "Fluency Score"]).reset_index(drop=True)
    return df


def create_progress_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a Plotly line chart for progress data.
    
    Ensures y-axis is 0-100 and handles empty or small datasets safely.
    """
    if df.empty or len(df) < 2:
        fig = px.line(title="Fluency Score Over Time")
        fig.update_layout(yaxis=dict(range=[0, 100]))
        return fig

    # Ensure matching lengths for plotting
    min_len = min(len(df['Date']), len(df['Fluency Score']))
    df = df.iloc[:min_len]

    fig = px.line(
        df,
        x="Date",
        y="Fluency Score",
        markers=True,
        title="Fluency Score Over Time"
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100]),
        xaxis_title="Date",
        yaxis_title="Fluency Score"
    )
    return fig