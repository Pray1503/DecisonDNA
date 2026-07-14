# Running DecisionDNA

This guide walks you through setting up, ingesting the database, running the Python FastAPI backend, launching the Next.js frontend dashboard, and running the test suite.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your system:
- **Python 3.10+**
- **Node.js 18+** & **npm**

---

## 🛠️ Step 1: Python Backend Setup & Virtual Environment

1. Open a terminal in the root directory of the project.
2. Create and activate a Python virtual environment:
   ```powershell
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment (Windows Powershell)
   .\venv\Scripts\activate

   # Activate the virtual environment (macOS/Linux)
   source venv/bin/activate
   ```
3. Install the required Python backend dependencies:
   ```powershell
   pip install fastapi uvicorn requests numpy scikit-learn sentence-transformers
   ```

---

## 🗄️ Step 2: Database Ingestion & Backfill

The backend uses a SQLite database (`data/decision_memory.db`) constructed from raw engineering data located in `OrgMemory-10K/`.

To ingest, normalize, and construct the decision records:
1. Ensure your virtual environment is active.
2. Run the backfill ingestion script:
   ```powershell
   python scripts/backfill.py
   ```
This script will:
- Parse all JSON files in the dataset (ADRs, Commits, PRs, Jira tickets, Datadog incidents, Slack logs).
- Normalize them into a universal schema.
- Extract relationships and construct the decision evidence graph.
- Save the result to `data/decision_memory.db`.

---

## 🚀 Step 3: Run the FastAPI Backend Server

To start the FastAPI development server:
1. From the project root, run:
   ```powershell
   python -m uvicorn app.main:app --port 8000 --reload
   ```
2. The API will be running at [http://localhost:8000](http://localhost:8000).
3. You can access the auto-generated Swagger API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 💻 Step 4: Run the Next.js Frontend Dashboard

To launch the web interface:
1. Navigate to the `frontend/` directory:
   ```powershell
   cd frontend
   ```
2. Install the frontend dependencies:
   ```powershell
   npm install
   ```
3. Start the Next.js development server:
   ```powershell
   npm run dev
   ```
4. The dashboard will be available at [http://localhost:3000](http://localhost:3000).

---

## 🧪 Step 5: Running Tests

The project includes test scripts located in the `scripts/` directory. You can run them to verify components are working correctly:

### 1. Test universal schema normalization
```powershell
python scripts/test_normalizer.py
```

### 2. Test evidence graph traversals and paths
```powershell
python scripts/test_graph.py
```

### 3. Test semantic embeddings similarity pipelines
```powershell
python scripts/test_semantic.py
```

### 4. Test live webhook ingestion process
```powershell
python scripts/test_webhook_ingest.py
```

### 5. Run end-to-end integration tests
```powershell
python scripts/test_end_to_end.py
```