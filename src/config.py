# ==============================
# src/config.py
# ==============================
# Configuration settings for the SpeakAura AI project.
# Loads environment variables from a .env file and provides
# centralized access to project, dataset, and model settings.

import os
from dotenv import load_dotenv

# -----------------------------
# Load Environment Variables
# -----------------------------
# Reads variables from a .env file in the project root
load_dotenv()

# -----------------------------
# Google Cloud Service Account
# -----------------------------
SERVICE_ACCOUNT_KEY_ID = os.getenv("SERVICE_ACCOUNT_KEY_ID")
SERVICE_ACCOUNT_KEY_FILE_PATH = os.getenv("SERVICE_ACCOUNT_KEY_FILE_PATH")

# -----------------------------
# Google Cloud Project Settings
# -----------------------------
PROJECT_ID = os.getenv("PROJECT_ID")
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER")
BUCKET_NAME = os.getenv("BUCKET_NAME")
CONNECTION_ID = os.getenv("CONNECTION_ID")

# -----------------------------
# BigQuery Dataset Settings
# -----------------------------
DATASET_ID = os.getenv("DATASET_ID")
DATASET_LOCATION = os.getenv("DATASET_LOCATION")

# -----------------------------
# BigQuery Table Names
# -----------------------------
AUDIO_OBJECT_TABLE_ID = os.getenv("AUDIO_OBJECT_TABLE_ID")
TRANSCRIBE_TABLE_ID = os.getenv("TRANSCRIBE_TABLE_ID")
ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID = os.getenv("ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID")
PDF_DATA_OBJECT_TABLE_ID = os.getenv("PDF_DATA_OBJECT_TABLE_ID")
PARSED_PDF_TABLE_ID = os.getenv("PARSED_PDF_TABLE_ID")
SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID = os.getenv("SPEECH_DOCUMENT_EMBEDDINGS_TABLE_ID")

# -----------------------------
# Speech-to-Text Model
# -----------------------------
SPEECH_MODEL_ID = os.getenv("SPEECH_MODEL_ID")
SPEECH_MODEL_NAME = os.getenv("SPEECH_MODEL_NAME")

# -----------------------------
# Generative AI (Gemini) Model
# -----------------------------
GENERATIVE_AI_MODEL = os.getenv("GENERATIVE_AI_MODEL")
GENERATIVE_AI_MODEL_ENDPOINT = os.getenv("GENERATIVE_AI_MODEL_ENDPOINT")

# -----------------------------
# Text Embedding Model
# -----------------------------
GENERATIVE_AI_EMBEDDING_MODEL_ID = os.getenv("GENERATIVE_AI_EMBEDDING_MODEL_ID")
GENERATIVE_AI_EMBEDDING_MODEL_ENDPOINT = os.getenv("GENERATIVE_AI_EMBEDDING_MODEL_ENDPOINT")

# -----------------------------
# Document AI Layout Parser
# -----------------------------
LAYOUT_PARSER_REMOTE_MODEL = os.getenv("LAYOUT_PARSER_REMOTE_MODEL")