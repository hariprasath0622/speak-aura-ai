# ==============================
# src/bigquery_utils/retrieval_qa.py
# ==============================
# Functions to generate text responses augmented by vector search
# using BigQuery ML (Generative AI + embeddings).
# ==============================
import pandas as pd
from google.cloud import bigquery
from src import config

def escape_for_sql(value: str) -> str:
        """Escape string for safe embedding into BigQuery SQL."""
        return value.replace("'", "''").replace("\n", "\\n")

def generate_text_with_vector_search(
    bq_client: bigquery.Client,
    user_question: str,
    top_k: int = 3,
    fraction_lists_to_search: float = 0.01,
    max_output_tokens: int = 2000,
    temperature: float = 0.2,
    top_p: float = 0.9
) -> str:
    """
    Generate AI text response augmented by vector search results.

    Args:
        bq_client: Initialized BigQuery client.
        user_question: User’s question to the AI assistant.
        top_k: Number of top similar documents to retrieve.
        fraction_lists_to_search: Fraction of candidate lists to search (for speed).
        max_output_tokens: Max tokens for LLM generation.
        temperature: LLM temperature for randomness.
        top_p: LLM top-p probability for nucleus sampling.

    Returns:
        str: Generated response from AI assistant.
    """
    
    # System prompt guiding AI behavior
    system_prompt = """
        You are a knowledgeable and supportive speech therapy assistant.
        Your role is to help people with stuttering and other speech disorders by:
        and Understand the User Question and answer what they want.
        Guidelines :
        - Using information from the provided Document Content when available.
        - If the context does not contain the answer, say so and give a helpful general suggestion.
        - Explaining therapy techniques in simple and practical terms.
        - Giving actionable advice that can be practiced at home.
        - Providing encouragement and empathy in responses.
        - Keeping answers concise, clear, and tailored to the user’s question.

        Answer in a professional, friendly, and supportive tone.
    """
    
    escaped_system_prompt = escape_for_sql(system_prompt)
    escaped_user_question = escape_for_sql(user_question)

    # Build the BigQuery ML.GENERATE_TEXT query with VECTOR_SEARCH
    query = f"""
    SELECT ml_generate_text_llm_result AS generated
    FROM ML.GENERATE_TEXT(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_MODEL}`,
        (
            SELECT CONCAT(
                '{escaped_system_prompt} and User Question: {escaped_user_question}',
                STRING_AGG(FORMAT('Document Content: %s', base.content))
            ) AS prompt
            FROM VECTOR_SEARCH(
                TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID}`,
                'text_embeddings',
                (
                    SELECT ml_generate_embedding_result, '{escaped_user_question}' AS query_text
                    FROM ML.GENERATE_EMBEDDING(
                        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
                        (SELECT '{escaped_user_question}' AS content)
                    )
                ),
                top_k => {top_k},
                options => '{{"fraction_lists_to_search": {fraction_lists_to_search}}}'
            )
        ),
        STRUCT({max_output_tokens} AS max_output_tokens, TRUE AS flatten_json_output)
    )
    """
    
    # Execute the query and return the generated response
    try:
        results = bq_client.query(query).result()
        row = next(results, None)
        return row.generated if row else "No answer generated."
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while generating the response."
    

def fetch_top_courses_vector_search(bq_client: bigquery.Client, user_query: str, top_k: int = 5, fraction_lists_to_search: float = 1.0) -> pd.DataFrame:
    """
    Fetch top-K courses based on vector similarity to user_query using Gemini embeddings and VECTOR_SEARCH.
    Embeddings are generated directly in BigQuery.

    Args:
        bq_client (bigquery.Client): Initialized BigQuery client
        user_query (str): Text query for which similar courses are retrieved
        top_k (int, optional): Number of top courses to return. Defaults to 5.
        fraction_lists_to_search (float, optional): Fraction of index lists to search. Defaults to 1.0.

    Returns:
        pd.DataFrame: DataFrame with columns: course_id, title, description, category, url, distance
    """
    user_query_easy = 'powerful speeches with confidence'
    query = f"""
    SELECT *
    FROM VECTOR_SEARCH(
        TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.COURSE_TABLE_ID}`,
        'course_embedding',
        (SELECT ml_generate_embedding_result
         FROM ML.GENERATE_EMBEDDING(
             MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
             (SELECT @query AS content)
         )
        ),
        top_k => {top_k},
        options => '{{"fraction_lists_to_search": {fraction_lists_to_search}}}'
    )
    """

    job = bq_client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("query", "STRING", user_query_easy)]
        )
    )

    df = job.to_dataframe()

    # Extract nested fields from the 'base' column
    df['course_id'] = df['base'].apply(lambda x: x['course_id'])
    df['title'] = df['base'].apply(lambda x: x['title'])
    df['description'] = df['base'].apply(lambda x: x['description'])
    df['category'] = df['base'].apply(lambda x: x['category'])
    df['url'] = df['base'].apply(lambda x: x['url'])

    # Keep only relevant columns
    df = df[['course_id', 'title', 'description', 'category', 'url', 'distance']]

    print(df.head())

    return df