# Project Context: AI-Powered Restaurant Recommendation System

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system intelligently suggests restaurants based on user preferences by combining **structured data** with a **Large Language Model (LLM)**.

---

## Objective

Design and implement an application that:

- Takes user preferences (location, budget, cuisine, ratings, etc.)
- Uses a real-world dataset of restaurants
- Leverages an LLM to generate personalized, human-like recommendations
- Displays clear and useful results to the user

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:
  - **Dataset URL:** https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation
- Extract relevant fields such as:
  - Restaurant name
  - Location
  - Cuisine
  - Cost
  - Rating
  - (and other applicable fields from the dataset)

### 2. User Input

Collect user preferences:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | User-defined threshold |
| **Additional preferences** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM **reason** and **rank** options

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants
- **Provide explanations** (why each recommendation fits the user's preferences)
- **Optionally summarize** choices

### 5. Output Display

Present top recommendations in a user-friendly format:

| Field | Description |
|-------|-------------|
| Restaurant Name | Name of the recommended restaurant |
| Cuisine | Type of cuisine offered |
| Rating | Restaurant rating |
| Estimated Cost | Approximate cost for two / per person (as per dataset) |
| AI-generated explanation | Why this restaurant was recommended |

---

## Key Technical Components

```
User Preferences → Data Filter → Structured Results → LLM Prompt → Ranked Recommendations → UI Output
```

| Component | Responsibility |
|-----------|----------------|
| **Dataset** | Hugging Face Zomato restaurant dataset |
| **Preprocessing** | Clean and extract structured fields |
| **Filtering** | Narrow candidates by location, budget, cuisine, rating |
| **LLM** | Rank, explain, and optionally summarize recommendations |
| **Frontend / Display** | Present results clearly to the user |

---

## Data Source

- **Platform:** Hugging Face Datasets
- **Dataset:** `ManikaSaini/zomato-restaurant-recommendation`
- **Link:** https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation

---

## Success Criteria

1. User can input preferences (location, budget, cuisine, minimum rating, extras).
2. System loads and uses the real Zomato dataset from Hugging Face.
3. Relevant restaurants are filtered before being sent to the LLM.
4. LLM returns ranked recommendations with human-readable explanations.
5. Output is displayed in a clear, user-friendly format with all required fields.

---

## Source

This context is derived from [`problemStatement.txt`](./problemStatement.txt).
