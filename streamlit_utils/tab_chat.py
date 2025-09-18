# ==============================
# src/tabs/tab_chat.py
# ==============================
# This file defines the "AI Therapy Chat" tab in Streamlit.
# Users can ask questions and receive responses from the AI Speech Therapist
# using vector search over BigQuery data.

from src.bigquery_utils.retrieval_qa import generate_text_with_vector_search

# ==============================
# RENDER FUNCTION
# ==============================
def render(tab, st, bq_client):
    """
    Render the "Chat With AI Speech Therapist" tab.

    Args:
        tab: Streamlit tab container
        st: Streamlit module
        bq_client: BigQuery client instance
    """
    with tab:
        # -----------------------------
        # Header
        # -----------------------------
        st.header("Chat With AI Speech Therapist")

        # -----------------------------
        # User Input Box
        # -----------------------------
        # Text input for user question; placeholder guides user
        user_input = st.text_input(
            "Ask a question:", 
            placeholder="Type your question here..."
        )

        # -----------------------------
        # Send Button Logic
        # -----------------------------
        if st.button("Send", key="chat_send"):
            if user_input.strip():  # Ensure input is not empty
                with st.spinner("Generating response using ML.GENERATE_TEXT()"):
                    # Generate AI response using BigQuery vector search
                    answer = generate_text_with_vector_search(
                        bq_client,
                        user_question=user_input
                    )

                # Display the AI response
                st.subheader("AI Speech Therapist Response")
                st.markdown(answer)
            else:
                # Warn if no input is provided
                st.warning("Please enter a question.")