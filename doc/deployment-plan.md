# Deployment Plan: CraveAI (Vercel & Render)

This document outlines the step-by-step procedure to deploy the decoupled architecture of the CraveAI restaurant recommendation system. We will host the **Next.js Frontend on Vercel** and the **FastAPI Backend on Render**.

## Architecture Overview
- **Frontend (Vercel)**: Next.js application handling the user interface and routing requests to the backend.
- **Backend (Render)**: Python FastAPI service running the retrieval logic and communicating with the Groq LLM API.
- **Data Layer**: The cleaned Zomato parquet file (`zomato_clean.parquet`) is checked into the Git repository and loaded into memory by the FastAPI backend on boot.

---

## Part 1: Repository Preparation

Before deploying, ensure your Git repository is ready:
1. **Dataset Tracking**: Ensure that `phase1/artifacts/zomato_clean.parquet` is **not** ignored in your `.gitignore` and is pushed to your remote repository. This allows the backend to access the data without downloading 600MB and re-running the ingest pipeline during deployment.
2. **Environment Variables Config**: Do not commit your `.env` file. We will configure secrets directly in the Vercel and Render dashboards.
3. **CORS Headers**: Ensure `backend/main.py` has CORS configured to allow your Vercel frontend URL (or `["*"]` for initial testing).

---

## Part 2: Backend Deployment (Render)

We will deploy the backend as a **Render Web Service** natively using Python.

### 1. Create a Render Web Service
1. Sign in to [Render.com](https://render.com) and link your GitHub account.
2. Click **New +** and select **Web Service**.
3. Select your CraveAI GitHub repository.

### 2. Configure Build and Run Commands
- **Name**: `craveai-backend` (or similar)
- **Region**: Select a region closest to your target audience.
- **Branch**: `main`
- **Root Directory**: Leave blank (or use `.` )
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### 3. Configure Environment Variables
Under the **Environment Variables** section, add the following:
- `GROQ_API_KEY`: *(Your Groq API Key)*
- `GROQ_MODEL`: `llama-3.3-70b-versatile`
- `PHASE1_PARQUET_PATH`: `phase1/artifacts/zomato_clean.parquet`

### 4. Deploy
Click **Create Web Service**. Render will install the dependencies, boot the server, and provide you with a public URL (e.g., `https://craveai-backend.onrender.com`).
*Note: Wait until the deployment succeeds and the health checks pass before proceeding to Part 3.*

---

## Part 3: Frontend Deployment (Vercel)

We will deploy the Next.js frontend using **Vercel**.

### 1. Create a Vercel Project
1. Sign in to [Vercel.com](https://vercel.com) and link your GitHub account.
2. Click **Add New... -> Project**.
3. Import your CraveAI repository.

### 2. Configure the Build
- **Project Name**: `craveai-frontend`
- **Framework Preset**: `Next.js`
- **Root Directory**: Click "Edit" and select the `frontend-next` folder.

### 3. Configure Environment Variables
Expand the **Environment Variables** section and add:
- `BACKEND_URL`: Paste your Render backend URL here (e.g., `https://craveai-backend.onrender.com`). *Ensure there is no trailing slash.*

### 4. Deploy
Click **Deploy**. Vercel will automatically build the Next.js application and assign it a production URL (e.g., `https://craveai-frontend.vercel.app`).

---

## Part 4: Post-Deployment Verification
1. **Test the Backend**: Navigate to `https://craveai-backend.onrender.com/api/v1/status` in your browser. You should receive a JSON response indicating the LLM is ready.
2. **Test the Frontend**: Navigate to your Vercel URL. Perform a search using realistic constraints (e.g., "North Indian", "High" budget, Location "Bellandur").
3. **Verify CORS**: If the frontend fails to fetch data, inspect the browser console. If there is a CORS error, you must update the `allow_origins` array in `backend/main.py` to include your exact Vercel URL, commit, and push to trigger a re-deployment on Render.
