# ==============================
# streamlit_utils/tab_analysis.py
# ==============================
# This file defines the "Stammer Analysis" tab in Streamlit.
# It displays the transcript, speech metrics, word-level breakdown,
# detected stammering patterns, and therapy suggestions.

import streamlit as st
import pandas as pd

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st):
    """
    Render the "AI-Powered Stammer Analysis & Therapy Suggestions" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("AI-Powered Stammer Analysis & Therapy Suggestions")

        # -----------------------------
        # Check if analysis exists in session state
        # -----------------------------
        if "current_analysis" in st.session_state and st.session_state.current_analysis:
            analysis = st.session_state.current_analysis

            # -----------------------------
            # Transcript
            # -----------------------------
            st.subheader("Transcript")
            st.write(analysis["transcript"])

            # -----------------------------
            # Speech Metrics
            # -----------------------------
            st.subheader("Speech Metrics")

            # Convert metrics dict to a DataFrame for display
            metrics_df = pd.DataFrame(analysis["metrics"], index=[0]).T
            metrics_df.columns = ["Value"]

            # Ensure all values are strings (fix Arrow conversion error)
            metrics_df["Value"] = metrics_df["Value"].astype(str)

            st.table(metrics_df)

            # -----------------------------
            # Word-Level Breakdown
            # -----------------------------
            st.subheader("Word-Level Breakdown")

           # Legend / color key
            st.markdown("""
            **Color Key:**  
            - 🟨 Yellow → Filler words (e.g., "uh", "um")  
            - 🟧 Orange → Repetitions  
            - 🟥 Red → Long pauses (>1.5 sec)  
            - 🟦 Blue → Prolongations (stretched sounds, e.g., "s-s-so")  
            """)
            
            df = analysis["words_df"].copy()

            # Highlight function for styling only certain columns
            def highlight_words(row):
                styles = [""] * len(row)  # default style
                cols_to_color = ["word", "start_time", "end_time", "pause"]

                if row["is_filler"]:
                    color = "background-color: yellow; font-weight: bold;"   # yellow
                elif row["is_repetition"]:
                    color = "background-color: orange; font-weight: bold;"   # orange
                elif row["is_block"]:
                    color = "background-color: red; font-weight: bold;"   # red
                elif row["is_prolongation"]:
                    color = "background-color: lightblue; font-weight: bold;"   # blue
                else:
                    return styles

                # Apply only to selected columns
                for col in cols_to_color:
                    if col in row.index:
                        styles[row.index.get_loc(col)] = color

                return styles

            st.dataframe(df.style.apply(highlight_words, axis=1))

            # -----------------------------
            # Detected Patterns
            # -----------------------------
            st.subheader("Detected Patterns")
            patterns = []

            if df["is_filler"].any():
                patterns.append("Frequent filler words (uh, um, etc.)")
            if df["is_repetition"].any():
                patterns.append("Word repetitions detected")
            if df["is_block"].any():
                patterns.append("Long pauses (>1.5s) detected")
            if df["is_prolongation"].any():
                patterns.append("Prolonged/stretched sounds detected")

            if patterns:
                for p in patterns:
                    st.markdown(f"- {p}")
            else:
                st.markdown("No major patterns detected.")

            # -----------------------------
            # Therapy Plan
            # -----------------------------
            st.subheader("Therapy Suggestions")
            st.write(analysis["therapy_plan"])

        else:
            # Inform user if analysis is not yet available
            st.info("Please record/upload and analyze audio in Tab 1 first.")