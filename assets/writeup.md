## Introduction

🔗 **Live Demo:** [Try SpeakAura AI](https://your-deployed-link.com)

## Stammering (or stuttering) is a speech disorder that affects approximately 70 million people worldwide, with 11–12 million in India alone. Among children, 5–8% experience temporary stammering, and while most recover by late childhood, about 1% persist into adulthood. Studies also indicate that self-reported stammering in adults may be as high as 2–4% in certain populations.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F17357389%2F6ec7f6edd92f85b62ed951cc66a4cd34%2FScreenshot%202025-09-17%20at%202.37.33AM.png?generation=1758056880954551&alt=media)

#### For people who stammer, the challenges go beyond speech:

- **Communication anxiety:** Fear of speaking in public, on phone calls, or during interviews.

- **Social stigma:** Concerns about being judged, bullied, or overlooked.

- **Career & education barriers:** Avoidance of leadership roles, oral exams, or client-facing jobs.

- **Limited therapy access:** Speech therapy is costly and unavailable in many regions.

- **Lack of progress tracking:** Therapists and patients struggle to objectively measure improvement.

Existing digital solutions often provide static exercises and lack personalization, leaving millions underserved.


## **Goal:**  

Develop a scalable AI solution that delivers personalized measurable and **accessible speech therapy** using **BigQuery AI**, 
                   **Vector Search** and **Generative AI** bridging the gap between clinical therapy and technology.

## **Impact Statement**

*SpeakAura AI helps millions of children and adults who stammer by providing affordable, accessible, and personalized therapy. It reduces therapy costs, increases confidence, and expands access in underserved regions — with the potential to impact ~70M people worldwide.*

- **For Individuals:** Affordable, at-home therapy support with measurable progress.

- **For Therapists:** Automated analysis + reports → reduces prep time by 40%+.

- **For Institutions (schools, clinics):** Scalable therapy support for children and adults.


## **Proposed Solution – SpeakAura AI**

  **SpeakAura AI**  is an AI-powered speech therapy assistant built on **BigQuery AI** that analyzes speech samples, detects stammering patterns, and generates personalized therapy plans — while tracking long-term progress.

**Features**

- **AI Voice Analyzer :** Detects stammer frequency, duration, and triggers in real-time.
- **Gamified Exercises:** Engaging, personalized drills for pacing, breathing, and conversation practice.
- **Virtual AI Coach:** Customizable encouraging feedback (users can select favorite voices or characters).
- **Progress Dashboard:** Tracks improvements objectively, sharing reports with users and therapists.
- **Multilingual Support in Future:** Therapy available in multiple languages as for this hackathon we focused on English only.

## **How It Works**

**Step-by-step Workflow:**

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F17357389%2F6adb56cc8c35c046678031ba4e489329%2FScreenshot%202025-09-16%20at%205.15.32PM.png?generation=1758053873181345&alt=media)



1. **Audio Upload**→ Cloud Storage → BigQuery Object Tables
2. **Transcription** → Vertex AI → BigQuery ML
3. **Word-level Analysis** → Extract disfluencies → Compute embeddings
4. **Vector Search** → Find similar cases → Guide therapy
5. **AI-Generated Therapy Plans** → Delivered to users
6. **Progress Tracking** → Dashboard → Therapist Feedback

**Multimodal Integration:**

Combines audio, transcripts, and therapy documents for holistic analysis

## Technical Implementation

SpeakAura AI leverages BigQuery AI to analyze speech, detect stammering patterns, and generate therapy plans.

**Data Pipeline Overview**

**1. Voice Input & Storage (Multimodal)**

- Users record speech samples via web app

- Audio files stored in Google Cloud Storage (GCS)

- Ingested into BigQuery Object Tables for analysis

**Speech Transcription**

- Speech-to-text performed using Vertex AI Speech-to-Text

- Transcripts flattened into word-level tables for analysis

```sql
       SELECT *
        FROM ML.TRANSCRIBE(
            MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.SPEECH_MODEL_ID}`,
            (
                SELECT uri, content_type
                FROM `{config.PROJECT_ID}.{config.DATASET_ID}.{config.AUDIO_OBJECT_TABLE_ID}`
                WHERE uri = '{gcs_uri}'
            ),
            RECOGNITION_CONFIG => (JSON '{config_str}')
        )
```
**Feature Extraction & Pattern Detection**

- Identify disfluency markers (pauses, repetitions, prolongations) using SQL + Python

- Extract embeddings with:

```sql
    SELECT ml_generate_embedding_result AS transcript_embedding
    FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
        (SELECT '{safe_transcript}' AS content),
        STRUCT(TRUE AS flatten_json_output)
    )
```

**Semantic Pattern Matching (Vector Search)**

- Find similar cases from historical speech data:

```sql
    SELECT 
        base.run_id,
        base.transcript,
        base.metrics,
        base.therapy_plan,
        base.processed_at,
        distance
    FROM VECTOR_SEARCH(
        TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.ANALYSIS_RESULTS_EMBEDDINGS_TABLE_ID}`,
        'transcript_embedding',
        (SELECT @embedding AS transcript_embedding),
        top_k => {top_k}
    )
    ORDER BY distance ASC;
```

**Personalized Therapy Plan Generation (Generative AI)**

- Generate scripts and exercises using AI.GENERATE:

```sql

  prompt = "Create a 5-minute practice script for a 10-year-old who stammers frequently on 's' sounds"

   SELECT AI.GENERATE(
        ('{therapy_prompt_safe}', ''),
        connection_id => 'us.{config.CONNECTION_ID}',
        endpoint => '{config.GENERATIVE_AI_MODEL_ENDPOINT}',
        output_schema => 'therapy_plan STRING'
    ).therapy_plan AS therapy_plan

```

**Progress Tracking Dashboards**

- Fetch forecasted fluency scores using AI.FORECAST from BigQuery.

- Dashboards display trends for user's latest disfluency frequency, Fillers, Sessions.

```sql
    SELECT
      forecast_timestamp,
      forecast_value AS fluency_forecast,
      prediction_interval_lower_bound,
      prediction_interval_upper_bound
    FROM
      AI.FORECAST(
        (
          SELECT 
            SAFE_CAST(JSON_VALUE(metrics, '$.severity_score') AS FLOAT64) * -100 + 100 AS fluency_score,
            processed_at
          FROM `bhack-471114.speakaura_ai_dataset.analysis_results_embeddings`
          ORDER BY processed_at
        ),
        data_col => 'fluency_score',
        timestamp_col => 'processed_at',
        horizon => {horizon},
        confidence_level => {confidence_level}
      );
```

**Domain-Specific Knowledge Integration**

- Therapy PDFs ingested into Object Tables

- Embeddings created for domain-specific guidance

- AI-generated exercises grounded in verified therapy content

```python
     SELECT * FROM ML.PROCESS_DOCUMENT(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.LAYOUT_PARSER_REMOTE_MODEL}`,
        TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.{config.PDF_DATA_OBJECT_TABLE_ID}`,
        PROCESS_OPTIONS => (JSON '{process_options}')
     )

    -----------------------------------------------------------------------------------------------------

    CREATE OR REPLACE TABLE `{temp_parsed_table}` AS
    SELECT
        uri,
        JSON_EXTRACT_SCALAR(json, '$.chunkId') AS chunk_id,
        JSON_EXTRACT_SCALAR(json, '$.content') AS content,
        CAST(JSON_EXTRACT_SCALAR(json, '$.pageSpan.pageStart') AS INT64) AS page_start,
        CAST(JSON_EXTRACT_SCALAR(json, '$.pageSpan.pageEnd') AS INT64) AS page_end
    FROM `{temp_process_table}`,
    UNNEST(JSON_EXTRACT_ARRAY(ml_process_document_result.chunkedDocument.chunks, '$')) AS json

   -------------------------------------------------------------------------------------------------------

    SELECT
        uri,
        chunk_id,
        content,
        page_start,
        page_end,
        ml_generate_embedding_result AS embedding
    FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.{config.GENERATIVE_AI_EMBEDDING_MODEL_ID}`,
        TABLE `{temp_parsed_table}`,
        STRUCT(TRUE AS flatten_json_output, 'RETRIEVAL_DOCUMENT' AS task_type)
    )
```

## **Practical Impact**


**Scenario 1: Child Practicing at Home**

- Child records 2-minute speech sample
- AI analyzes disfluencies and generates gamified exercises
- Dashboard shows improvement over 4 weeks

**Scenario 2: Professional Preparing for Interview**

- Uploads a sample of presentation speech
- AI highlights filler words and suggests personalized scripts
- Embeddings identify similar successful practice patterns

**Scenario 3: Therapist Monitoring Patients**

- Reviews AI-generated dashboards for multiple patients
- Adjusts therapy remotely, focusing on high-priority issues


## **Customers & Revenue Model**

- **Freemium App:** Free basic version, premium for advanced analytics & AI coach.

- **B2C Subscription:** Monthly/annual plans for individual users.

- **B2B Partnerships:** Schools, universities, and hospitals integrate SpeakAura AI.

- **Therapist SaaS:** Subscription dashboards for monitoring multiple patients.


## **Why SpeakAura AI is Unique**

Unlike existing apps or traditional therapy, Speak Aura AI combines:

- ✅ **Generative AI** → dynamic, personalized practice scripts.

- ✅ **Vector Search** → deep speech pattern matching.

- ✅ **Multimodal AI** → audio  + therapist notes.

- ✅ **BigQuery Analytics** → objective, Fitbit-style fluency tracking.

- ✅ **Hybrid Mode** → supports therapists, doesn’t replace them.

This makes SpeakAura AI not just an app, but a data-driven therapy ecosystem.


## **Comparison Table**

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F17357389%2F34cf83842d22e9a3058fa7b879a4a466%2FScreenshot%202025-09-17%20at%202.45.56AM.png?generation=1758057381987958&alt=media)


## **References:**

[Stuttering Foundation](https://www.stutteringhelp.org/)\
[STAMMA Research](https://stamma.org/features/how-many-adults-stammer)\
[Action for Stammering Children](https://stamma.org/)