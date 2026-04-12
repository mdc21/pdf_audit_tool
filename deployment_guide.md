# Deployment & Packaging Guide: Kompare Audit Suite

This guide provides the definitive steps for setting up the **Kompare Audit Suite** in a local or production environment. It covers the orchestration of the AI layer, the forensic database, and the analytics frontend.

## 1. Architecture Overview
Kompare operates on a decentralized, agentic architecture:
- **Frontend (UI)**: Streamlit-based analytics dashboard (Python).
- **Inference Engine (AI)**: Local LLM orchestration via Ollama.
- **Persistence (DB)**: PostgreSQL 17 relational database for forensic audit history.
- **Agentic Layer**: Decoupled background workers for asynchronous business insights.

---

## 2. Prerequisites
Ensure you have the following installed before proceeding:
- **Python 3.9 - 3.12**: Core runtime.
- **Docker & Docker Compose**: For containerized infrastructure.
- **Ollama**: (Required for LLM inference).
- **Git**: For version control management.

---

## 3. Infrastructure Orchestration (One-Click)
The suite uses Docker to provide a standardized environment for the database and AI services.

### 3.1. Launching the Containers
From the project root, execute:
```bash
docker-compose up -d
```
This command initializes:
1.  **PostgresDB**: Accessible on port `5432`.
2.  **Ollama Service**: Accessible on port `11434`.

### 3.2. Verifying Health
- **Database**: Run `docker ps` to ensure the `db` service is "Up".
- **AI Layer**: Run `curl http://localhost:11434/api/tags` to verify Ollama accessibility.

---

## 4. AI Model Preparation (Critical)
The Kompare engine is optimized for the **Qwen 2.5 (7B)** model weight to balance high-speed inference with hardware stability on local machines.

```bash
# Pull the standardized model weight
ollama pull qwen2.5:7b
```

> [!IMPORTANT]
> Ensure you have at least 8GB of free RAM available for the localized inference worker.

---

## 5. Local Application Installation
Once the infrastructure is live, set up the Python environment:

```bash
# 1. Create a dedicated virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Upgrade pip and install core dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Configuration & Environment
The suite is pre-configured to point to `localhost`. If you are running the database on a remote host, update the `DATABASE_URL` in `models.py`.

### 6.1. Parallel Worker Configuration
Open the **Kompare UI Sidebar** to adjust:
- **Parallel Threads (Audit)**: Recommended: 4 (for fast technical diffing).
- **Parallel AI Workers**: Recommended: 1 (for stable background business analysis).

---

## 7. Execution: Launching the Suite

To start the institutional audit dashboard, run:
```bash
streamlit run app.py
```

---

## 8. Forensic Operations & Maintenance

### 8.1. Log Management
All forensic system actions, including AI reasoning and database transactions, are recorded in:
- `pdf_audit.log` (Characterized by `[filename:funcName]` metadata).
- **Tip**: Run `tail -f pdf_audit.log` during batch audits for real-time observability.

### 8.2. Troubleshooting
- **AI Query Fails**: Verify the Ollama container is running and the model `qwen2.5:7b` has been pulled.
- **Database Connection Reset**: Ensure the Docker container is healthy and no local Postgres instance is conflicting on port `5432`.

### 8.3. Governance
The **History Dashboard** serves as your permanent repository. Ensure you do not delete the `postgres_data` Docker volume if you wish to preserve multi-release history.
