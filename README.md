# Speak Aura AI

A speech analysis tool that identifies and analyzes stammering patterns using **Google Cloud BigQuery AI**.  
Our solution empowers individuals with speech disfluencies to **track progress, receive personalized therapy plans, and compare their journey with similar cases** — all powered by **SQL + AI**.

---

## 🚀 Overview

- 🎤 Upload speech audio → stored in **Google Cloud Storage**  
- 📝 Transcribe + analyze → processed in **BigQuery AI**  using ML.transcribe
- 📊 Detect stammering metrics (pauses, repetitions, fillers)  
- 🧠 Generate personalized therapy guidance with **Gemini**  using AI.GENERATE
- 🔍 Find similar cases using **vector search** embeddings  using ML.GENERATE_EMBEDDING AND VECTOR_SEARCH
- 🔮 Forecast future fluency scores with **AI.FORECAST**  using AI.FORECAST (This creates a **feedback loop** where users can **monitor, compare, and improve** their speech patterns over time.)  

---

## 🏗️ Architecture


![Architecture Diagram](assets/speak_aura_architecture.png)



## Architecture

?

## How Our Solution Uses BigQuery AI

### 🖼️ Multimodal Pioneer
- Built a **BigQuery Object Table** referencing audio files stored in GCS.  
- This allows us to **treat raw audio as queryable data in SQL**, bridging **unstructured (audio)** with **structured (transcripts + metrics)** seamlessly.  

### 🕵️ Semantic Detective
- Generated **embeddings** with **`ML.GENERATE_EMBEDDING`** and performed **`VECTOR_SEARCH`** in BigQuery.  
- This enables our app to **find similar past speech cases**, so users can compare their journey with others and learn from proven strategies.  

### 🧠 AI Architect
- Applied **`AI.FORECAST`** to predict **future fluency scores**, giving users a forward-looking view of their speech progress.  
- Used **`AI.GENERATE (Gemini)`** to create **personalized therapy plans** based on transcript + stammering metrics.  

---
✅ By combining **forecasting, semantic search, and multimodal analysis**, our solution demonstrates the **full spectrum of BigQuery AI capabilities** in one integrated workflow.  

## Project Setup

## 1. Set up Google Cloud Project credentials

1. Make sure you have a Google Cloud Project.  
2. Create or download a service account key with the required permissions in IAM in GCP.  
3. put the server account key json under the credentials folder and use that path in required env variable

## 2. Create a .env file

1. Copy from `.env-template` → `.env` 
2. Fill in required values (project, dataset, bucket, etc).

## 3. Set up GCP resources and permissions

1. Open the notebook:

``` bash

notebooks/gcp_resource_setup.ipynb

```
2. Run all cells to configure IAM roles + connections.

## 4. Create a virtual environment

``` bash
python -m venv aura_env
source aura_env/bin/activate 
# On Windows: venv aura_env\Scripts\activate

```
## 5. Install dependencies

``` bash
pip install -r requirements.txt

```

## 6. Create project resources

1. Open a terminal and navigate to the src folder:

``` bash
cd src
```
2. Run the resource creation script:
``` bash
python -m create_resource.create_resource
```

## 7. Run the project

1. Open a new terminal.
2. Make sure you are in the root folder of the project.
3. Launch the Streamlit app

``` bash
streamlit run streamlit_app.py
```

## Project Structure

```
speak-aura-ai/
│── credentials/             # GCP service account keys
├── data/
│   ├── audio/               # Sample input audio files
│   └── transcripts/         # Sample transcripts to use while recording
├── notebooks/
│   └── gcp_resource_setup.ipynb   # Setup IAM + GCP resources
├── src/
│   ├── create_resource/     # Scripts to set up GCS/BigQuery
│   ├── analyze_stammer.py   # Detect stammering in text
│   ├── bigquery_utils.py    # All BigQuery query helpers
│   ├── client.py            # GCP client initialization
│   ├── config.py            # Project configs (IDs, buckets)
│   ├── pipeline.py          # Orchestrates data → analysis
│   └── upload_audio.py      # Upload audio → GCS bucket
├── streamlit_utils/
│   ├── tab_upload.py        # UI: Upload audio
│   ├── tab_analysis.py      # UI: Stammer analysis
│   ├── tab_semantic.py      # UI: Similar case search
│   ├── tab_progress.py      # UI: Forecast & progress
│   ├── tab_about.py         # UI: About section
│   └── streamlit_helpers.py # Shared UI helpers
├── tests/
│   └── test_transcribe.py   # Unit tests for transcription
│── .env                     # Local env vars
│── .env-template.txt        # Env var template
│── .gitignore               # Git ignore rules
│── README.md                # Project documentation
│── requirements.txt         # Python dependencies
└── streamlit_app.py         # Main Streamlit entrypoint

```

## Reference code

 https://github.com/GoogleCloudPlatform/generative-ai/tree/e3fdeae53809fadc60887f3c0411c00510cfe561/gemini/use-cases/applying-llms-to-data


## License
