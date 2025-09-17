# ==============================
# streamlit_utils/tab_semantic.py
# ==============================
# This file defines the "Semantic Detective" tab in Streamlit.
# Users can find similar past cases using semantic embeddings
# and BigQuery vector search.

import streamlit as st
import json
from src.bigquery_utils.embeddings import fetch_similar_cases

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st, bq_client):
    """
    Render the "Semantic Detective: Find Similar Past Cases" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
        bq_client: BigQuery client instance
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("🕵️ Semantic Detective: Find Similar Past Cases")

        # -----------------------------
        # Check if transcript & embedding exist
        # -----------------------------
        if (
            "current_analysis" in st.session_state and st.session_state.current_analysis and
            "current_transcript_embedding" in st.session_state and st.session_state.current_transcript_embedding
        ):
            # Display user's transcript
            st.subheader("Your Transcript")
            st.write(st.session_state.current_analysis["transcript"])

            # -----------------------------
            # Find similar cases button
            # -----------------------------
            if st.button("🔍 Find Similar Cases"):
                with st.spinner("Running semantic search in BigQuery..."):
                    try:
                        # Fetch top-k similar cases using vector search
                        similar_df = fetch_similar_cases(
                            bq_client,
                            st.session_state.current_transcript_embedding,
                            top_k=3
                        )
                    except Exception as e:
                        st.error(f"Error fetching similar cases: {e}")
                        return

                # -----------------------------
                # Display results
                # -----------------------------
                if not similar_df.empty:
                    st.success(f"✅ Found {len(similar_df)} similar past cases:")
                    for i, row in similar_df.iterrows():
                        st.markdown(f"### Case {i+1} (distance={row['distance']:.4f})")
                        st.write(f"**Transcript:** {row['transcript']}")
                        # Try to display metrics as JSON
                        try:
                            metrics_json = json.loads(row['metrics'])
                            st.json(metrics_json)
                        except Exception:
                            st.write(row['metrics'])
                        st.markdown("**Therapy Plan:**")
                        st.write(row['therapy_plan'])
                        st.markdown("---")
                else:
                    st.warning("No similar cases found in the database yet.")
        else:
            # Inform user if analysis or embedding is missing
            st.info("Please record/upload and analyze audio in Tab 1 first.")