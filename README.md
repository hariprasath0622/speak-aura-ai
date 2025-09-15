# Speak Aura AI

A speech analysis tool that helps identify and analyze stammering patterns using Google Cloud Platform services.

## Overview

This project uses Google Cloud's BigQuery AI to analyze speech patterns and identify stammering instances in audio recordings.

## Architecture

?

## Project Setup

## 1. Set up Google Cloud Project credentials

1. Make sure you have a Google Cloud Project.  
2. Create or download a service account key with the required permissions in IAM in GCP.  
3. put the server account key json under the credentials folder and use that path in required env variable

## 2. Create a .env file

1. Copy all variables from .env-template into a new .env file.
2. Fill in all required values for your environment.

## 3. Set up GCP resources and permissions

1. Open the notebook:

``` bash

notebooks/gcp_resource_setup.ipynb

```
2. Run all cells to configure IAM roles and connection permissions.

## 4. Create a virtual environment

``` bash
python -m venv aura_env
source venv aura_env/bin/activate 
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


## Project Structure

```
speak-aura-ai/
│
│── credentials              # store the service account key json
├── data/
│   ├── audio/              # Sample audio files (user test input)
│   └── transcripts/        # Output transcripts for testing
│
├── notebooks/
│   └── gcp_resource_setup.ipynb    # note book to setup IAM permission and connection for Vertex AI and GCS
│
├── src/
├── create_resource/
│   └───── create_resource.py/              # code to setup all the resource to run the project like  gcs , bigquery - datasets,tables,models
│   ├── __init__.py
│   ├── analyze_stammer.py # Highlight stammering patterns
│   ├── bigquery_utils.py  # All bigquery queries used for this project
│   ├── client.py          # Setup clients for bigquery,speech etc..
│   ├── config.py          # Config (project_id, dataset_id, GCS bucket etc...)
│   ├── pipeline.py        # Orchestrate the full flow
│   └── upload_audio.py    # Upload user audio → GCS
├──streamlit_utils/
│   ├─  __init__.py
│   ├─ tab_upload.py
│   ├─ tab_analysis.py
│   ├─ tab_semantic.py
│   ├─ tab_progress.py
│   ├─ tab_about.py
│   └── streamlit_helpers.py 
├── tests/
│    └── test_transcribe.py # Unit tests
│── .env    
│──  env-template.txt    
│── .gitignore    
│── README.md                # Overview, setup, hackathon writeup link
│── requirements.txt         # Python dependencies
└── streamlit_app.py         # main application - start of the flow 

```



## Reference code

 https://github.com/GoogleCloudPlatform/generative-ai/tree/e3fdeae53809fadc60887f3c0411c00510cfe561/gemini/use-cases/applying-llms-to-data


## License
