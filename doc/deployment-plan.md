# Deployment Plan: CraveAI (Vercel & Railway)

This document outlines the step-by-step procedure to deploy the decoupled architecture of the CraveAI restaurant recommendation system. We will host the **Next.js Frontend on Vercel** and the **FastAPI Backend on Railway**.

## Architecture Overview
- **Frontend (Vercel)**: Next.js application handling the user interface and routing requests to the backend.
- **Backend (Railway)**: Python FastAPI service running the retrieval logic and communicating with the Groq LLM API.
- **Data Layer**: The cleaned Zomato parquet file (`zomato_clean.parquet`) is checked into the Git repository and loaded into memory by the FastAPI backend on boot.

---

## Part 1: Repository Preparation

Before deploying, ensure your Git repository is ready:
1. **Dataset Tracking**: Ensure that `phase1/artifacts/zomato_clean.parquet` is **not** ignored in your `.gitignore` and is pushed to your remote repository.
2. **Environment Variables Config**: Do not commit your `.env` file. We will configure secrets directly in the Vercel and Railway dashboards.
3. **CORS Headers**: `backend/main.py` has CORS configured to allow `["*"]`.
4. **Procfile**: A `Procfile` is present at the root of the repository so Railway knows how to start the FastAPI server.

---

## Part 2: Backend Deployment (Railway)

We will deploy the backend natively using Python on Railway.

### 1. Create a Railway Service
1. Sign in to [Railway.app](https://railway.app/) and link your GitHub account.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your CraveAI GitHub repository.
4. Click **Deploy Now**. (The initial build will start, but you need to add environment variables).

### 2. Configure Environment Variables
1. Click on the newly created CraveAI service card in the Railway dashboard.
2. Go to the **Variables** tab.
3. Add the following:
   - `GROQ_API_KEY`: *(Your Groq API Key)*
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - `PHASE1_PARQUET_PATH`: `phase1/artifacts/zomato_clean.parquet`

### 3. Expose the Public URL
1. Go to the **Settings** tab of your service.
2. Under **Networking**, click **Generate Domain** (or set up a custom domain). 
3. Copy this URL (e.g., `https://craveai-backend-production.up.railway.app`). You will need it for the frontend.

*Railway will automatically rebuild and deploy your application with the new environment variables and public domain.*

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
- `BACKEND_URL`: Paste your Railway backend URL here (e.g., `https://craveai-backend-production.up.railway.app`). *Ensure there is no trailing slash.*

### 4. Deploy
Click **Deploy**. Vercel will automatically build the Next.js application and assign it a production URL (e.g., `https://craveai-frontend.vercel.app`).

---

## Part 4: Post-Deployment Verification
1. **Test the Backend**: Navigate to your Railway URL `.../api/v1/status` in your browser. You should receive a JSON response indicating the LLM is ready.
2. **Test the Frontend**: Navigate to your Vercel URL. Perform a search using realistic constraints (e.g., "North Indian", "High" budget, Location "Bellandur").
