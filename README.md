# AI Powered Data Cleaning
An AI-assisted data cleaning application that analyzes tabular datasets,

detects data-quality issues, generates cleaning recommendations, and

lets the user approve or reject those recommendations before any

cleaning operation is executed.

### 🚀 Live Demo

[**Try the AI Data Cleaner →**](https://ai-data-cleaner.streamlit.app/)

The project is designed around a **human-in-the-loop** approach: AI

provides analysis and recommendations, while the actual data

transformation is performed by a deterministic Python cleaning engine

only after user approval.

---

## Overview
Data cleaning is often repetitive and requires decisions about how

missing values, duplicate records, inconsistent categories, and outliers

should be handled.

This project combines:

-   **Python and Pandas** for deterministic data processing

-   **FastAPI** for the backend API

-   **Streamlit** for the web interface

-   **Gemini** for AI-generated cleaning recommendations

-   **Pydantic** for structured proposal validation

-   **Pytest** for automated testing

The system separates **detection**, **recommendation**, **approval**,

and **execution** so that detecting a problem never automatically means

modifying the dataset.

---

## Key Features
### Dataset ingestion
Supports:

-   CSV files

-   Excel `.xlsx` files

-   Excel `.xls` files

Uploaded files are assigned UUID-based filenames in the backend's

raw-data directory.

### Dataset profiling
The application builds a profile containing information such as:

-   Number of rows

-   Number of columns

-   Column names

-   Data types

-   Missing values

-   Duplicate rows

-   Numerical columns

-   Categorical columns

### Data-quality detection
The system detects:

-   Missing values

-   Duplicate rows

-   Potential outliers using the IQR method

-   Inconsistent categorical values using normalized comparison

Detection only produces evidence. It does not automatically modify the

dataset.

### AI cleaning recommendations
The AI receives structured dataset and quality information and generates

recommendations containing:

-   Issue type

-   Cleaning operation

-   Affected columns

-   Affected values when available

-   Detection method

-   Evidence

-   Interpretation

-   Recommended action

-   Confidence

-   Reason

The AI is restricted to the cleaning operations supported by the

application.

### Human-in-the-loop approval
Every recommendation must be reviewed before execution.

Depending on the recommendation, the user can:

-   Approve or reject a non-destructive recommendation

-   Keep or remove data for recommendations requiring review

The backend validates that every recommendation has exactly one valid

decision before creating a cleaning request.

### Deterministic cleaning engine
After approval, the actual cleaning is performed by the Python cleaning

engine.

Supported operations include:

-   Median imputation for numerical missing values

-   Mode imputation for categorical missing values

-   Category standardization

-   Outlier removal

-   Duplicate-row removal

The cleaning engine does not execute arbitrary AI-generated code or SQL.

### Cleaning audit and report
After cleaning, the application reports:

-   Rows before cleaning

-   Rows after cleaning

-   Rows removed

-   Missing values filled

-   Duplicate rows removed

-   Outliers removed

-   Standardized columns

The cleaned dataset can then be downloaded from the application.

---

## System Architecture
``` text

                         ┌──────────────────────┐

                         │     Streamlit UI     │

                         │      Frontend        │

                         └──────────┬───────────┘

                                    │

                                    ▼

                         ┌──────────────────────┐

                         │       FastAPI        │

                         │       Backend        │

                         └──────────┬───────────┘

                                    │

                ┌───────────────────┴───────────────────┐

                │                                       │

                ▼                                       ▼

       ┌─────────────────┐                    ┌──────────────────┐

       │ Data Processing │                    │    AI Engine     │

       │                 │                    │                  │

       │ File Ingestion  │                    │ Gemini           │

       │ Profiling       │                    │ Proposal         │

       │ Issue Detection │                    │ Generation       │

       │ Cleaning        │                    │ Validation       │

       └────────┬────────┘                    └────────┬─────────┘

                │                                      │

                └──────────────────┬───────────────────┘

                                   ▼

                         ┌──────────────────────┐

                         │  Human Approval      │

                         │  / Decision Layer    │

                         └──────────┬───────────┘

                                    │

                                    ▼

                         ┌──────────────────────┐

                         │ Deterministic        │

                         │ Cleaning Engine      │

                         └──────────┬───────────┘

                                    │

                                    ▼

                         ┌──────────────────────┐

                         │ Audit + Cleaning     │

                         │ Report               │

                         └──────────┬───────────┘

                                    │

                                    ▼

                         ┌──────────────────────┐

                         │ Cleaned CSV          │

                         │ Download             │

                         └──────────────────────┘

```

---

## End-to-End Workflow
``` text

Upload Dataset

      │

      ▼

Load CSV / Excel

      │

      ▼

Profile Dataset

      │

      ▼

Detect Quality Issues

      │

      ▼

Build Structured AI Input

      │

      ▼

Generate Cleaning Proposal

      │

      ▼

Validate Proposal

      │

      ▼

Show Recommendations

      │

      ▼

User Reviews Each Recommendation

      │

      ▼

Create Approved Cleaning Request

      │

      ▼

Execute Deterministic Cleaning

      │

      ▼

Generate Audit / Report

      │

      ▼

Download Cleaned Dataset

```

---

## Project Structure
``` text

AI POWERED DATA CLEANING/

│

├── backend/

│   ├── ai/

│   │   ├── approval.py

│   │   ├── decision.py

│   │   ├── gemini_proposal_generator.py

│   │   ├── input_schema.py

│   │   ├── proposal.py

│   │   ├── proposal_converter.py

│   │   └── proposal_generator.py

│   │

│   ├── cleaning/

│   │   ├── duplicates.py

│   │   ├── missing_values.py

│   │   ├── outliers.py

│   │   ├── pipeline.py

│   │   ├── report.py

│   │   ├── request.py

│   │   └── standardization.py

│   │

│   ├── ingestion/

│   │   ├── csv_loader.py

│   │   ├── excel_loader.py

│   │   └── file_loader.py

│   │

│   ├── profiling/

│   │   ├── profile.py

│   │   └── quality.py

│   │

│   ├── utils/

│   │   └── config.py

│   │

│   └── main.py

│

├── frontend/

│   └── app.py

│

├── tests/

│   ├── test_approval.py

│   ├── test_components.py

│   ├── test_gemini_proposal.py

│   ├── test_proposal_flow.py

│   └── test_recommendation_v2.py

│

├── data/

│   ├── raw/

│   └── processed/

│

├── .env

├── .gitignore

├── README.md

├── requirements.txt

└── test_gemini_38.py

```

\> The exact project tree may change as development continues. Temporary

\> development files and local environment files should not be committed

\> to the public repository.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Backend | FastAPI |
| Frontend | Streamlit |
| AI | Google Gemini |
| Validation | Pydantic |
| Machine Learning Utilities | Scikit-learn |
| Excel Processing | OpenPyXL |
| Environment Variables | python-dotenv |
| Testing | Pytest |
| API Server | Uvicorn |

---

## Supported Cleaning Operations

| Operation | Purpose |
|---|---|
| Median Imputation | Fill missing numerical values using the column median |
| Mode Imputation | Fill missing categorical values using the column mode |
| Standardization | Normalize inconsistent categorical formatting |
| Outlier Removal | Remove rows containing IQR-based outlier values |
| Duplicate Removal | Remove exact duplicate rows |

The application validates the requested operation and its column compatibility before execution.

---

## AI Recommendation Design
The AI does not directly clean the uploaded dataset.

Instead, the system follows:

``` text

Dataset

   ↓

Profiling

   ↓

Issue Detection

   ↓

Issue Analysis

   ↓

AI Recommendation

   ↓

Human Decision

   ↓

Cleaning Request

   ↓

Deterministic Cleaning

```

This separation provides an important safety boundary between

AI-generated recommendations and actual data modification.

The AI is asked to return structured JSON, which is then validated

against the application's proposal schema before it can participate in

the approval workflow.

---

## Gemini Integration
The project supports Gemini as the AI recommendation provider.

The application can use:

-   A primary Gemini model

-   A configured fallback Gemini model

The integration includes handling for:

-   Structured JSON responses

-   Proposal validation

-   Server-side retry behavior

-   Primary-model quota/server failures

-   Fallback-model execution

API credentials are loaded through environment variables and should

never be hard-coded into the source code.

---

## API Workflow
The backend exposes the main workflow through endpoints including:

### `GET /`
Checks that the API is running.

### `POST /analyze`
Accepts an uploaded dataset and returns:

-   Dataset profile

-   Quality issues

-   AI cleaning proposal

### `POST /approve`
Accepts the user's recommendation decisions and converts them into a

deterministic cleaning request.

### `POST /execute-cleaning`
Executes the approved cleaning request and generates the cleaned dataset

and report.

### `GET /download/{filename}`
Downloads a generated cleaned CSV file.

---

## Running the Project Locally
### 1. Clone the repository
``` bash

git clone https://github.com/gupta-krishna13/AI-Powered-Data-Cleaner.git

cd AI-Powered-Data-Cleaner

```

### 2. Create and activate a virtual environment
Windows:

``` bash

python -m venv ai_data_cleaner_env

ai_data_cleaner_env\Scripts\activate

```

### 3. Install dependencies
``` bash

pip install -r requirements.txt

```

### 4. Configure environment variables
Create a `.env` file in the project root:

``` env

APP_ENV=development

AI_MODE=gemini

GEMINI_API_KEY=your_gemini_api_key

GEMINI_MODEL=your_primary_model

GEMINI_FALLBACK_MODEL=your_fallback_model

```

Never commit the `.env` file or expose the API key publicly.

### 5. Start the FastAPI backend
From the project root:

``` bash

uvicorn backend.main:app --reload

```

The backend will run locally on:

``` text

http\://127.0.0.1:8000

```

### 6. Start the Streamlit frontend
Open another terminal, activate the same virtual environment, and run:

``` bash

streamlit run frontend/app.py

```

The Streamlit application will display its local URL in the terminal.

---

## Testing
The project includes automated tests covering major parts of the

recommendation and approval workflow.

Run:

``` bash

pytest

```

The Gemini integration test is intentionally separated from the normal

test suite so that routine testing does not unnecessarily consume Gemini

API quota.

To explicitly run the Gemini integration test:

Windows CMD:

``` cmd

set RUN_GEMINI_TEST=1

pytest tests/test_gemini_proposal.py

```

Do not enable the integration test unnecessarily during normal

development.

---

## Security and Validation
Several safeguards are implemented in the current version:

-   Uploaded files receive UUID-based backend filenames.

-   Approval requests validate the supplied raw-data filename.

-   Download filenames are validated against path traversal.

-   Download paths are resolved and checked to remain inside the

    processed-data directory.

-   Cleaning operations are restricted to supported operations.

-   Recommendation columns are validated against the uploaded dataset.

-   Operation/column compatibility is validated before execution.

-   Every recommendation must receive exactly one valid decision before

    approval.

-   AI-generated proposals are validated before being used.

-   API keys are stored through environment variables rather than source

    code.

---

## Error Handling
The application handles common failure scenarios such as:

-   Missing or invalid files

-   Unsupported file types

-   Empty files

-   Malformed CSV input

-   Backend connection failures

-   Invalid recommendation decisions

-   Incomplete approval requests

-   Invalid cleaning operations

-   Missing columns

-   Invalid download filenames

The frontend also clears stale analysis state when an analysis request

fails, preventing results from a previous dataset from remaining visible

after an error.

---

## Testing Scenarios
The project has been manually tested with scenarios including:

-   Clean datasets

-   Datasets containing missing values

-   Duplicate rows

-   Outliers

-   Inconsistent categories

-   Multiple simultaneous data-quality issues

-   Multiple affected columns

-   Recommendation approval/rejection

-   Keep/remove decisions

-   Incomplete approval decisions

-   Large recommendation sets

-   Malformed CSV files

-   Empty CSV files

-   One-column datasets

-   Datasets with unusual column names

-   Backend unavailable scenarios

-   Download and path-validation behavior

---

## Design Principles
### 1. Detection is not cleaning
Finding an issue does not automatically mean that the system should

modify the data.

### 2. AI recommends, deterministic code executes
The AI proposes an action. The Python cleaning engine performs the

actual transformation.

### 3. Human approval before modification
The user remains in control of every recommendation.

### 4. Structured communication
AI output is converted into a validated proposal schema instead of being

treated as arbitrary executable code.

### 5. Auditable cleaning
The system records what happened during cleaning so the user can inspect

the result.

---

## Current Limitations
This is currently a Version 1 application.

Some production-level features are intentionally outside the current

scope, including:

-   User authentication and accounts

-   Persistent analysis history

-   Production database-backed job storage

-   Advanced file-size/content security limits

-   Production deployment configuration

-   Advanced dataset lineage and version management

-   Large-scale distributed processing

These can be considered in later versions.

---

## Future Improvements
Possible future development includes:

-   User authentication

-   Persistent cleaning history

-   Database-backed job management

-   More data-quality detectors

-   Additional cleaning strategies

-   Better dataset visualization

-   More advanced anomaly detection

-   Background processing for large datasets

-   Cloud deployment

-   Production-grade file storage

-   Dataset versioning

-   Exportable cleaning reports

-   More configurable AI models

-   Improved monitoring and observability

---

## Project Philosophy
The goal of this project is not simply to build an AI that automatically

changes a dataset.

The goal is to build a system where AI can \*\*understand data-quality

problems, explain its recommendations, and assist the user in making

cleaning decisions\*\*, while deterministic code performs the approved

transformations.

``` text

AI Analysis

     ↓

Explanation

     ↓

Human Decision

     ↓

Deterministic Execution

     ↓

Auditable Result

```

This makes the system easier to understand, test, and control than an

approach where an AI model directly modifies user data.

---

## Status

**Version 1 — Deployed**

Core ingestion, profiling, quality detection, AI recommendation, human
approval, deterministic cleaning, reporting, frontend workflow,
validation, automated testing, and deployment are implemented.

The FastAPI backend is deployed on Render and the Streamlit frontend is
deployed on Streamlit Community Cloud.

### Live Demo

[**Try the AI Data Cleaner →**](https://ai-data-cleaner.streamlit.app/)

---

## Author
**Krishna Gupta**

Built as a project exploring AI-assisted data analysis, data quality,

human-in-the-loop systems, and deterministic data-processing workflows.
