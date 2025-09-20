# ==============================
# tab_recommended_courses.py
# ==============================

import streamlit as st
import random
import tempfile
from streamlit_mic_recorder import mic_recorder
# ==============================
# Course Recommendation
# ==============================

def render(tab):
    with tab:
        st.header("🎓 Recommended Courses Based on Your Speech Analysis")
        
        st.markdown("---")

        st.warning(
    "⚠️ **Beta Feature / Concept:** The exercises and course recommendations are an **experimental idea** for demonstration purposes. "
            "They are meant to give users a sense of what’s possible and may not reflect final functionality."
        )

        if "current_top_courses" not in st.session_state:
            st.info("Run a stammer analysis first to see course recommendations.")
            return
        
        # ------------------------------
        # Recommended Courses
        # ------------------------------

        top_courses = st.session_state.current_top_courses

        if top_courses.empty:
            st.warning("No recommended courses found. Try again with a different analysis.")
            return

        # Display courses already in session state
        for _, row in top_courses.iterrows():
            st.subheader(row["title"])
            st.write(row["description"])
            st.markdown(f"[🔗 Course Link]({row['url']})")
            st.divider()


        # ------------------------------
        # Gamified Exercises
        # ------------------------------

        st.subheader("🎮 Gamified Interactive Exercises")

        if "current_analysis" not in st.session_state:
            st.info("Run a speech analysis to generate exercises.")
            return
        
        # ------------------------------
        # Define exercises based on severity
        # ------------------------------

        analysis = st.session_state.current_analysis
        severity = analysis.get("metrics", {}).get("severity_score", 0)

        # Define exercises
        exercises = []
        if severity < 0.3:
            exercises = [
                {"task": "Read aloud a short story in 2 minutes.", "points": 10},
                {"task": "Explain your daily routine in 1 minute.", "points": 15},
            ]
        elif severity < 0.6:
            exercises = [
                {"task": "Practice breathing pauses after every sentence.", "points": 20},
                {"task": "Read a paragraph avoiding filler words.", "points": 25},
            ]
        else:
            exercises = [
                {"task": "Repeat 5 tongue-twisters slowly, then faster.", "points": 30},
                {"task": "Record a 1-minute self-introduction.", "points": 35},
            ]

        # Initialize session state
        if "exercise_points" not in st.session_state:
            st.session_state.exercise_points = 0
        if "current_exercise" not in st.session_state:
            st.session_state.current_exercise = 0
        if "completed_exercises" not in st.session_state:
            st.session_state.completed_exercises = []

        # Stop if all exercises are done
        if st.session_state.current_exercise >= len(exercises):
            st.success(f"🎉 All exercises completed! Total Points Earned: {st.session_state.exercise_points}")
            return

        current_index = st.session_state.current_exercise
        ex = exercises[current_index]

        # Only show exercise if not completed
        if current_index not in st.session_state.completed_exercises:
            st.markdown(f"**Exercise {current_index + 1}/{len(exercises)}:** {ex['task']}")

            audio_data = mic_recorder(
                start_prompt="🎤 Start Recording",
                stop_prompt="⏹ Stop Recording",
                just_once=True,
                key=f"exercise_{current_index}"
            )

            if audio_data:
                # Save audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_data["bytes"])
                    st.session_state.local_path = tmp.name

                st.audio(st.session_state.local_path, format="audio/wav")

                earned_points = random.randint(ex['points'] - 5, ex['points'])
                st.session_state.exercise_points += earned_points
                st.success(f"🎉 Exercise Completed! You earned {earned_points} points.")

                # Mark exercise as completed
                st.session_state.completed_exercises.append(current_index)

        # Next Exercise button
        if st.session_state.current_exercise in st.session_state.completed_exercises:
            if st.button("➡️ Next Exercise", key=f"next_ex_{current_index}"):
                st.session_state.current_exercise += 1
                st.rerun()  # updated

        st.markdown(f"**🏆 Total Points Earned:** {st.session_state.exercise_points}")