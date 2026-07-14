# Smart Pharmacy Platform - Production Deployment Guide

This document defines the production-ready architecture, containerization configuration, and deployment roadmap to run the **Smart Pharmacy Inventory Platform** on cloud infrastructure (like Google Cloud Platform, AWS, or Azure).

---

## 🏛️ 1. Enterprise System Architecture
The platform is built using a clean, decoupled full-stack architecture:
*   **Frontend Client**: Light-weight, responsive Streamlit application running client-side. Calls backend REST APIs.
*   **FastAPI Backend Server**: ASGI web application handling API routes, OAuth2 JWT auth, role validation, Excel/CSV cleansers, and ML predictions.
*   **Relational Database**: PostgreSQL database storing relational tables (Users, Medicines, Alerts, etc.).
*   **Redis Cache**: Caching session data and ML job states.

```mermaid
graph TD
    A["Web Browser / Client UI"] -->|HTTPS| B["Reverse Proxy / Load Balancer<br>(NGINX / GCP Load Balancer)"]
    B -->|Route Client| C["Streamlit Client Container<br>(Port 8501)"]
    B -->|Route API| D["FastAPI Backend Container<br>(Port 8000)"]
    
    D -->|JWT Validation| E["OAuth2 & RBAC Middleware"]
    D -->|Cache Query| F["Redis Cache Container"]
    D -->|Query Data| G["Relational Database<br>(PostgreSQL Cloud SQL)"]
```

---

## 🐳 2. Containerized Deployment (Docker Compose)
We define the container stack in `docker-compose.yml` to launch the database, cache, and backend server simultaneously.

### Running Container Stack locally:
1.  Verify Docker and Docker Compose are installed.
2.  Set up environment properties in `.env`.
3.  Launch the services:
    ```bash
    docker-compose up --build
    ```
    This automatically builds the FastAPI app container, starts Postgres, spins up Redis, and exposes the backend API gateway at `http://localhost:8000`.

---

## ☁️ 3. Google Cloud Platform (GCP) Deployment Guide

This system is optimized for Google's "Build with AI: Code for Communities" Hackathon and is designed to run seamlessly on Google Cloud.

### Step 1: Deploy PostgreSQL Database (Cloud SQL)
1.  Go to the GCP Console and create a **Cloud SQL for PostgreSQL** instance.
2.  Create a database named `pharmacy_db`.
3.  Configure database credentials (username and password).
4.  Enable the **Cloud SQL Auth Proxy** for secure connections.

### Step 2: Deploy FastAPI Backend to Google Cloud Run
1.  Build the backend container image and submit it to **Google Artifact Registry**:
    ```bash
    gcloud builds submit --tag gcr.io/your-project-id/pharmacy-backend:latest -f backend/Dockerfile .
    ```
2.  Deploy the container to **Google Cloud Run**:
    ```bash
    gcloud run deploy pharmacy-backend \
        --image gcr.io/your-project-id/pharmacy-backend:latest \
        --platform managed \
        --region asia-south1 \
        --allow-unauthenticated \
        --set-env-vars DATABASE_URL=postgresql://user:password@cloud-sql-ip:5432/pharmacy_db \
        --set-env-vars JWT_SECRET=your_jwt_secret_hash \
        --set-env-vars GEMINI_API_KEY=your_google_gemini_api_key
    ```
3.  Record the generated Cloud Run service URL (e.g. `https://pharmacy-backend-xxx.run.app`).

### Step 3: Deploy Streamlit Frontend Client
1.  Modify `frontend/streamlit_app.py` environment to point to the backend URL:
    ```bash
    # Set environment variable
    $env:API_URL="https://pharmacy-backend-xxx.run.app/api/v1"
    ```
2.  Containerize and push the Streamlit client to Cloud Run or App Engine:
    ```bash
    gcloud run deploy pharmacy-frontend \
        --image gcr.io/your-project-id/pharmacy-frontend:latest \
        --set-env-vars API_URL=https://pharmacy-backend-xxx.run.app/api/v1
    ```

---

## 🔒 4. Production Security Hardening
Before launching in production:
*   **Disable Swagger UI**: In `backend/app/main.py`, disable docs by setting `docs_url=None` and `redoc_url=None` if settings env is set to `production`.
*   **CORS Origins**: Replace `allow_origins=["*"]` in `main.py` with your explicit Streamlit frontend domain.
*   **Secrets Manager**: Store `DATABASE_URL`, `JWT_SECRET`, and `GEMINI_API_KEY` in **Google Secret Manager** instead of plain text environment variables.
