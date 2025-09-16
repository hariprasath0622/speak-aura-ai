# src/tabs/tab_chat.py
from src.bigquery_utils import generate_text_with_vector_search

def render(tab, st, bq_client):
    with tab:
        st.header("💬 AI Chat")

        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Display previous conversation
        for qa in st.session_state.chat_history:
            st.markdown(f"**You:** {qa['q']}")
            st.markdown(f"**AI:** {qa['a']}")

        # Input box
        user_input = st.text_input("Ask a question:", placeholder="Type your question here...")

        if st.button("Send", key="chat_send"):
            if user_input.strip():
                with st.spinner("Generating response..."):
                    answer = generate_text_with_vector_search(
                        bq_client,
                        user_question=user_input
                    )

                # Save in chat history
                st.session_state.chat_history.append({"q": user_input, "a": answer})
                st.experimental_rerun()
            else:
                st.warning("Please enter a question.")
