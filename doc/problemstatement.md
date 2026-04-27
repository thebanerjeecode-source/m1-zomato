# Problem Statement: AI‑Powered Restaurant Recommendation System (Zomato Use Case)

Build an AI-powered restaurant recommendation application inspired by Zomato. The system should generate personalized, human-friendly restaurant recommendations by combining **structured restaurant data** with a **Large Language Model (LLM)**.

## Objective
Design and implement an application that:
- Accepts user preferences (e.g., **location**, **budget**, **cuisine**, **minimum rating**, and optional constraints such as **family-friendly** or **quick service**)
- Uses a real-world restaurant dataset
- Filters candidates using deterministic logic and then uses an LLM to **rank** and **explain** recommendations
- Presents results in a clear, user-friendly format

## Dataset
Use the Zomato restaurant recommendation dataset from Hugging Face:
- `https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation`

The system should ingest and preprocess the dataset and extract relevant fields such as:
- Restaurant name
- Location / city
- Cuisine(s)
- Cost (or cost category)
- Rating (or rating category)
- Any other useful metadata available in the dataset

## Inputs
Collect user preferences including:
- **Location** (e.g., Delhi, Bangalore)
- **Budget** (e.g., low / medium / high, or a numeric range if supported)
- **Cuisine** (e.g., Italian, Chinese)
- **Minimum rating**
- **Additional preferences** (optional; examples: family-friendly, quick service)

## Expected Output
Return the top recommendations with:
- **Restaurant name**
- **Cuisine**
- **Rating**
- **Estimated cost**
- **LLM-generated explanation** describing why the option matches the user’s preferences

## High-Level Workflow
1. **Data ingestion**
   - Load and preprocess the dataset
   - Normalize key fields (location, cuisines, price, rating)
2. **User input**
   - Gather user preferences from the UI/API
3. **Integration layer (retrieval + prompt preparation)**
   - Apply rule-based filtering to select relevant candidates
   - Prepare a structured shortlist to send to the LLM
   - Construct a prompt that enables comparison, ranking, and justification
4. **Recommendation engine (LLM)**
   - Rank shortlisted restaurants
   - Generate concise explanations for each choice
   - Optionally produce a short summary of trade-offs
5. **Output display**
   - Present results in a consistent, readable UI/format

## Assumptions and Constraints
- The dataset is the source of truth for restaurant metadata used in recommendations.
- The LLM should not hallucinate restaurants not present in the dataset shortlist.
- Recommendations should be reproducible to the extent possible given the same inputs (e.g., fixed shortlist + stable prompt).
