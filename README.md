# 🍽️ Zomato AI Recommender

A premium AI-powered restaurant discovery platform built with Python, FastAPI, and Streamlit, utilizing the Groq LLaMA 3.3 model and a Zomato dataset from Hugging Face.

## 📖 Overview

The Zomato AI Recommender acts as a "Culinary Intelligence System", blending deterministic hard-filtering (to ensure location, budget, and rating constraints are respected) with LLM-powered semantic reasoning to pick the best options and explain *why* they fit your preferences.

- **Frontend**: A visually stunning, modern Streamlit interface designed with a dark-mode premium aesthetic.
- **Backend API**: A FastAPI service exposing endpoints for recommendation queries and metadata extraction.
- **AI Engine**: Uses Groq's high-speed inference for near-instant LLaMA 3.3 reasoning.
- **Resilience**: Features a fallback engine, anti-hallucination guardrails, and an offline Parquet cache fallback in case Hugging Face or the LLM goes offline.

*For deeper insights, see the [Context & Goals](docs/context.md), [System Architecture](docs/architecture.md), and [Edge Cases & Error Scenarios](docs/edge-case.md) documentation.*

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- A [free Groq API key](https://console.groq.com/keys)

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd Zomato-Milestone1
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file from the provided example:
```bash
cp .env.example .env
```
Open `.env` and paste your Groq API key:
```env
GROQ_API_KEY=gsk_your_real_key_here
```

### 3. Generate Local Dataset Cache (Optional but recommended)
To ensure the app works blazingly fast and offline, generate the Parquet cache once:
```bash
python scratch/generate_parquet.py
```

---

## 🏃 Running the Application

You can use the provided `Makefile` to run the various components.

### Start the Premium Frontend (Streamlit)
```bash
make ui
```
*This will open the app in your browser at `http://localhost:8501`*

### Start the Backend API (FastAPI)
If you just want the REST API:
```bash
make api
```
*API docs will be available at `http://localhost:8000/docs`*

---

## 🧪 Testing

The project includes a robust suite of 94 automated tests covering core logic, Edge Cases, Anti-Hallucination, and LLM Resilience.

Run the test suite:
```bash
make test
```

---

## 🏗️ Architecture Summary

1. **Data Ingestion**: Loads Hugging Face `ManikaSaini/zomato-restaurant-recommendation` with fallback to local Parquet/JSON cache.
2. **Filtering Pipeline**: Applies deterministic filters (location, budget tier, cuisine, min rating). Uses an automated "relaxation waterfall" if zero matches are found.
3. **LLM Engine**: Prompts Groq with a strict JSON-mode schema.
4. **Anti-Hallucination Guard**: Intercepts the LLM response, verifying that no "fake" restaurants were hallucinated, and fixes missing schema fields.
5. **Fallback Engine**: If the LLM rate-limits or fails, automatically switches to a deterministic ranking system so the user *always* gets recommendations.
