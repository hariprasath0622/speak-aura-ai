# streamlit_utils/tab_analysis.py

import streamlit as st
import pandas as pd

def render(tab, st):
    with tab:
        st.header("AI-Powered Stammer Analysis & Therapy Suggestions")

        if "current_analysis" in st.session_state and st.session_state.current_analysis:
            analysis = st.session_state.current_analysis

            # Transcript
            st.subheader("Transcript")
            st.write(analysis["transcript"])

            # Metrics
            st.subheader("Speech Metrics")
            metrics_df = pd.DataFrame(analysis["metrics"], index=[0]).T
            metrics_df.columns = ["Value"]
            st.table(metrics_df)

            # Word-level breakdown
            st.subheader("Word-Level Breakdown")
            df = analysis["words_df"].copy()

            def highlight_words(row):
                if row.get("is_filler"):
                    return ["background-color: yellow"] * len(row)
                elif row.get("is_repetition"):
                    return ["background-color: orange"] * len(row)
                elif row.get("long_pause"):
                    return ["background-color: red"] * len(row)
                else:
                    return [""] * len(row)

            st.dataframe(df.style.apply(highlight_words, axis=1))

            # Detected Patterns
            st.subheader("Detected Patterns")
            patterns = []
            if df["is_filler"].any():
                patterns.append("Frequent filler words (uh, um, etc.)")
            if df["is_repetition"].any():
                patterns.append("Word repetitions detected")
            if df["long_pause"].any():
                patterns.append("Long pauses (>1.5s) detected")

            if patterns:
                for p in patterns:
                    st.markdown(f"- {p}")
            else:
                st.markdown("No major patterns detected.")

            # Therapy Plan
            st.subheader("Therapy Suggestions")
            st.write(analysis["therapy_plan"])

        else:
            st.info("Please record/upload and analyze audio in Tab 1 first.")