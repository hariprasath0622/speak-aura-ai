# ==============================
# streamlit_utils/tab_progress.py
# ==============================
# This file defines the "Progress Dashboard" tab in Streamlit.
# Users can view historical fluency scores, key metrics,
# and forecast future progress using AI.

import streamlit as st
import pandas as pd
from streamlit_utils.streamlit_helpers import create_progress_chart, create_forecast_chart, build_progress_df
from src.bigquery_utils.forecasting import fetch_progress_data, fetch_forecast

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st, bq_client):
    """
    Render the "Track Your Progress" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
        bq_client: BigQuery client instance
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("📊 Track Your Progress")

        # -----------------------------
        # Initialize session state variables
        # -----------------------------
        if "progress_loaded" not in st.session_state:
            st.session_state.progress_loaded = False
        if "progress_df" not in st.session_state:
            st.session_state.progress_df = pd.DataFrame()
        if "forecast_requested" not in st.session_state:
            st.session_state.forecast_requested = False
        if "forecast_df" not in st.session_state:
            st.session_state.forecast_df = pd.DataFrame()

        # -----------------------------
        # Load progress button
        # -----------------------------
        if st.button("📊 Load My Progress"):
            try:
                results_df = fetch_progress_data(bq_client)
                if not results_df.empty:
                    # Convert BigQuery results into structured DataFrame
                    st.session_state.progress_df = build_progress_df(results_df)
                    st.session_state.progress_loaded = True
                else:
                    st.info("No progress data found yet. Record your first session to see progress.")
            except Exception as e:
                st.error(f"Error fetching progress: {e}")

        # -----------------------------
        # Display progress if loaded
        # -----------------------------
        if st.session_state.progress_loaded and not st.session_state.progress_df.empty:
            progress_df = st.session_state.progress_df

            # -----------------------------
            # Key Performance Indicators (KPIs)
            # -----------------------------
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest Fluency", f"{progress_df['Fluency Score'].iloc[-1]}%")
            col2.metric("Avg Fillers", f"{progress_df['Filler Count'].mean():.1f}")
            col3.metric("Sessions Completed", len(progress_df))

            # -----------------------------
            # Progress chart
            # -----------------------------
            st.plotly_chart(create_progress_chart(progress_df), width="stretch")

            # -----------------------------
            # Forecast button
            # -----------------------------
            if st.button("🔮 Forecast Progress"):
                st.session_state.forecast_requested = True

            # -----------------------------
            # Show forecast if requested
            # -----------------------------
            if st.session_state.forecast_requested:
                with st.spinner("Running AI.FORECAST..."):
                    try:
                        # Fetch forecast data from BigQuery
                        st.session_state.forecast_df = fetch_forecast(
                            bq_client, horizon=10, confidence_level=0.8
                        )

                        # Display forecast chart
                        st.subheader("Forecasted Improvement")
                        fig = create_forecast_chart(progress_df, st.session_state.forecast_df)
                        st.plotly_chart(fig, width="stretch")

                        # Show forecasted data as table
                        st.dataframe(st.session_state.forecast_df, width="stretch")
                    except Exception as e:
                        st.error(f"Error generating forecast: {e}")
        else:
            # Inform user to load progress first
            st.info("Click **Load My Progress** to view your progress dashboard.")