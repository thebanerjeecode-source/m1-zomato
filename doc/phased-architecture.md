# Phase‑Wise Architecture: AI‑Powered Restaurant Recommendation System

This document breaks the system into incremental phases so each phase delivers a testable slice of functionality and de-risks later work (data quality, retrieval, LLM prompting, UI, evaluation, deployment).

## Overall Target Architecture (end state)
- **Client/UI**: collects preferences, displays ranked recommendations and explanations.
- **API Service**: validates inputs, orchestrates retrieval + LLM ranking, returns structured results.
- **Data Layer**:
  - **Dataset ingestion pipeline** (offline or scheduled): downloads + cleans + normalizes Zomato dataset.
  - **Restaurant store**: a local file (CSV/Parquet/SQLite) and later optional search index/vector store.
- **Retrieval/Filtering**: deterministic filtering by location/budget/cuisine/rating; optional semantic matching.
- **LLM Layer**:
  - Prompt builder that supplies a **bounded shortlist** of restaurants.
  - Guardrails to prevent hallucination beyond shortlist.
- **Observability/Evaluation**: logs, metrics, offline evaluation set, and prompt/version tracking.

---

## Phase 0 — Skeleton + Contract (Hello, end‑to‑end without real data)
**Goal**: Establish the repo structure, interfaces, and a working “demo” flow using a tiny hardcoded sample.

- **Deliverables**
  - Project structure (e.g., `api/`, `ui/`, `data/`, `docs/`).
  - A minimal API endpoint, e.g. `POST /recommendations`, with a stable request/response schema.
  - A basic web UI (simple form) as the **primary source of user input** for Phase 0.
  - Stub dataset of ~10 restaurants embedded as JSON for initial wiring.
  - Deterministic filtering + simple ranking (no LLM yet).
- **Key components**
  - `InputSchema` (location, budget, cuisine, minRating, additionalPreferences)
  - `Restaurant` model (name, location, cuisines, cost, rating, metadata)
  - `Recommendation` model (restaurant fields + explanation string)
- **Exit criteria**
  - Given a user preference payload, API returns top \(N\) recommendations in the expected output shape.

---

## Phase 1 — Data Ingestion (real dataset → normalized store)
**Goal**: Download and preprocess the Hugging Face dataset into a clean, queryable format.

- **Deliverables**
  - Dataset downloader (Hugging Face datasets client or direct download).
  - Preprocessing pipeline:
    - Normalize city/location strings
    - Parse cuisines into an array
    - Normalize cost and rating (handle missing/invalid values)
    - De-duplicate rows if needed
  - Persisted dataset artifact (choose one):
    - **CSV/Parquet** for simplicity, or
    - **SQLite** for easy filtering/sorting
- **Key components**
  - `ingest/download_dataset`
  - `ingest/clean_transform`
  - `storage/write_dataset` + `storage/read_dataset`
- **Exit criteria**
  - A reproducible ingestion run produces a dataset file committed to `.gitignore` and generated locally.
  - Basic query confirms required fields exist and are usable.

---

## Phase 2 — Retrieval & Rule‑Based Filtering (deterministic shortlist)
**Goal**: Replace the stub dataset with the real normalized store and implement robust filtering.

- **Deliverables**
  - Filtering rules:
    - Location match (exact/normalized; optional partial match)
    - Budget range/category mapping to dataset’s cost field
    - Cuisine match (exact/contains; handle multi-cuisine)
    - Minimum rating threshold
  - Shortlist builder:
    - Returns top \(K\) candidates using a deterministic scoring function
    - Handles missing values and edge cases (no matches, too many matches)
  - Consistent sorting strategy (e.g., rating desc, cost proximity, cuisine match strength)
- **Key components**
  - `retrieval/filter_candidates(preferences) -> List[Restaurant]`
  - `retrieval/score_and_select(candidates) -> shortlist(K)`
- **Exit criteria**
  - For a variety of inputs, shortlist generation is stable and fast.
  - API returns meaningful results without LLM involvement.

---

## Phase 3 — LLM Ranking + Explanations (bounded, non-hallucinating)
**Goal**: Introduce the LLM to rank the deterministic shortlist and generate explanations while preventing hallucinations.

- **Deliverables**
  - Prompt builder that provides:
    - User preferences
    - A JSON (or bullet) **shortlist of \(K\)** restaurants with fields
    - Explicit instruction: “Only reference restaurants from the provided shortlist”
  - LLM response parser:
    - Structured output (recommended: JSON schema) containing ordered ids/names + explanations
    - Validation that returned restaurants exist in shortlist
  - Fallback strategy:
    - If LLM fails/returns invalid output, fall back to deterministic ranking + templated explanation
- **Key components**
  - `llm/build_prompt(preferences, shortlist)`
  - `llm/call_model(prompt)`
  - `llm/validate_and_parse(response, shortlist)`
- **Exit criteria**
  - Output contains ranked restaurants + concise explanations that match user constraints.
  - Hard guarantee: no restaurants outside shortlist appear in the final response.

---

## Phase 4 — UI / UX (user input + results display)
**Goal**: Provide a user-friendly interface to collect preferences and display results.

- **Deliverables**
  - Basic web UI:
    - Inputs: location, budget, cuisine, min rating, additional preferences
    - “Get Recommendations” action
    - Results list/cards with explanation
  - Client-side validation and loading/error states
- **Key components**
  - `ui/preferences_form`
  - `ui/results_view`
  - `ui/api_client`
- **Exit criteria**
  - A non-technical user can get recommendations end-to-end via UI.

---

## Phase 5 — Evaluation, Edge Cases, and Guardrails
**Goal**: Make the system reliable and measurable.

- **Deliverables**
  - Edge case handling:
    - No matches → suggest relaxing constraints (lower rating, expand budget, nearby cuisines)
    - Missing dataset fields → safe defaults
    - Conflicting preferences → explain trade-offs
  - Offline evaluation set (handwritten scenarios) + expected properties:
    - “Should include only city X”
    - “Should not exceed budget”
    - “Must meet min rating when possible”
  - Prompt/version tracking and basic telemetry:
    - Log request inputs, shortlist size, LLM latency, validation failures
- **Exit criteria**
  - Repeatable evaluation run with pass/fail checks for key constraints.
  - Observable failures and graceful fallbacks.

---

## Phase 6 — Decoupled Architecture (Backend & Frontend Separation)
**Goal**: Transition from a basic embedded UI to a modern, fully decoupled frontend and backend to support scalability and a richer user experience.

- **Deliverables**
  - **Backend (REST API)**:
    - FastAPI refactored into a standalone API service (e.g., `backend/`).
    - Implementation of proper CORS, versioned API routing (`/api/v1/...`), and structured error handling.
  - **Frontend (Web App)**:
    - A dedicated modern frontend (e.g., React, Next.js, or Vite) housed in a separate `frontend/` directory.
    - Implementation of modern UI/UX design (rich aesthetics, dynamic animations, modern typography).
    - Robust state management for search queries, loading overlays, and result rendering.
  - **Integration**:
    - OpenAPI/Swagger serving as the definitive contract between frontend and backend.
    - Local development setup to run both services concurrently.
- **Exit criteria**
  - Frontend and backend run as distinct services communicating over HTTP.
  - The UI provides a premium, responsive experience independent of the backend serving logic.

---

## Phase 7 — Deployment & Production Hardening (optional)
**Goal**: Prepare the decoupled architecture for real usage.

- **Deliverables**
  - Containerization (Docker) with separate containers for frontend and backend (e.g., via Docker Compose).
  - Environment-based config, secrets handling for LLM keys.
  - Caching (optional): shortlist caching per query hash.
  - Rate limiting + input sanitization.
  - Monitoring dashboards/alerts (latency, error rate, LLM failures).
- **Exit criteria**
  - One-command deployable artifact and documented runbook.

---

## Phase 8 — Streamlit Deployment (Alternative UI)
**Goal**: Provide a lightweight, Python-only alternative frontend for rapid prototyping and deployment using Streamlit.

- **Deliverables**
  - **Streamlit App**:
    - A single-file frontend (`app.py` or `streamlit_app.py`) that collects user preferences using Streamlit widgets.
    - Direct integration with the FastAPI backend via HTTP requests, or alternatively, importing the backend logic directly if running as a monolith.
  - **Deployment Setup**:
    - Configuration for free hosting platforms like Streamlit Community Cloud or Hugging Face Spaces.
    - Updated `requirements.txt` to include `streamlit`.
- **Exit criteria**
  - A fully functional Streamlit frontend deployed online and accessible via a public URL, communicating with the backend to serve recommendations.

---

## Recommended Interfaces (stable contracts)
- **Request**: preferences object (location, budget, cuisine, minRating, additionalPreferences)
- **Response**: list of recommendations with restaurant fields + explanation
- **Internal**:
  - `IngestedDataset -> CandidateRetriever -> Shortlist -> LLMRanker -> Presenter`

