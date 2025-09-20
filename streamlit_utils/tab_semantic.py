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
            # User input: number of similar cases
            # -----------------------------
            num_cases = st.number_input(
                "How many similar cases would you like to see?",
                min_value=1,
                max_value=5,
                value=1,
                step=1
            )

            # -----------------------------
            # Find similar cases button
            # -----------------------------
            if st.button("🔍 Find Similar Cases"):
                with st.spinner("Running VECTOR_SEARCH() in BigQuery..."):
                    try:
                        # Fetch top-k similar cases using user input
                        similar_df = fetch_similar_cases(
                            bq_client,
                            st.session_state.current_transcript_embedding,
                            top_k=num_cases
                        )
                    except Exception as e:
                        st.error(f"Error fetching similar cases: {e}")
                        return

                # -----------------------------
                # Display results
                # -----------------------------
                st.markdown("---")
                if not similar_df.empty:
                    st.success(f"✅ Found {len(similar_df)} similar past cases:")

                    for i, row in similar_df.iterrows():
                        with st.container():
                            st.markdown(
                                f"""
                                <div style="
                                    background: linear-gradient(135deg, #1E3A8A, #2563EB); 
                                    padding:15px; 
                                    border-radius:12px; 
                                    margin-bottom:15px; 
                                    box-shadow:0 4px 10px rgba(0,0,0,0.25); 
                                    max-width: 320px;">
                                    <h3 style="color:#FFFFFF; margin:0; font-size:30px; font-weight:600;">
                                        Case {i+1}
                                    </h3>
                                    <p style="color:#FFFFFF; font-size:20px; margin:5px 0 0;">
                                        Similarity Distance: <b>{row['distance']:.4f}</b>
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Case details in two columns
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.markdown("**📝 Transcript**")
                                st.info(row['transcript'])

                                st.markdown("**📋 Therapy Plan**")
                                st.write(row['therapy_plan'])

                            with col2:
                                st.markdown("**📊 Metrics**")
                                try:
                                    metrics_json = json.loads(row['metrics'])
                                    st.json(metrics_json)
                                except Exception:
                                    st.warning("⚠️ Metrics not in JSON format")
                                    st.write(row['metrics'])

                            st.markdown("---")

                else:
                    st.warning("No similar cases found in the database yet.")
        else:
            # Inform user if analysis or embedding is missing
            st.info("Please record/upload and analyze audio in Tab 1 first.")