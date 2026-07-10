import os
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.webhooks import router as webhook_router
from app.core.memory import DecisionMemory
from app.core.query_agent import QueryAgent

app = FastAPI(
    title="DecisionDNA Dashboard API",
    description="Backend API for querying, browsing, and inspecting reconstructed engineering decisions.",
    version="1.0.0"
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook router
app.include_router(webhook_router)

# Paths
DB_PATH = Path("data/decision_memory.db")
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)


def get_db():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Decision Memory database not initialized. Run reconstruction first."
        )
    return DecisionMemory(db_path=DB_PATH)


# --------------------------------------------------
# CORE API ENDPOINTS
# --------------------------------------------------

@app.get("/api/stats")
async def get_stats():
    """
    Returns counts of artifacts, relationships, decisions, and system projects.
    """
    if not DB_PATH.exists():
        return {
            "decisions": 0,
            "artifacts": 0,
            "relationships": 0,
            "projects": 0,
            "slack": 0,
            "incidents": 0,
            "deployments": 0,
            "initialized": False
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM artifacts")
        art_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships")
        rel_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM decisions")
        dec_count = cursor.fetchone()[0]

        # Specific type counts
        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'chat'")
        slack_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'incident'")
        incident_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'deployment'")
        deployment_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'issue' AND source = 'jira'")
        jira_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'commit'")
        commit_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM artifacts WHERE source_type = 'pull_request'")
        pr_count = cursor.fetchone()[0]

        # Estimate unique projects/repositories
        cursor.execute("SELECT DISTINCT json_extract(context, '$.project') FROM artifacts WHERE source_type = 'adr'")
        projects = [row[0] for row in cursor.fetchall() if row[0]]
        
        if not projects:
            cursor.execute("SELECT DISTINCT json_extract(context, '$.repository') FROM artifacts WHERE source_type = 'commit'")
            projects = [row[0] for row in cursor.fetchall() if row[0]]

        conn.close()

        return {
            "decisions": dec_count,
            "artifacts": art_count,
            "relationships": rel_count,
            "projects": len(projects) or 25,
            "slack": slack_count,
            "incidents": incident_count,
            "deployments": deployment_count,
            "jira": jira_count,
            "commits": commit_count,
            "prs": pr_count,
            "initialized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")


@app.get("/api/decisions")
async def list_decisions(search: Optional[str] = None):
    """
    List all reconstructed decisions. Optionally searches via keyword scoring.
    """
    db = get_db()
    if search:
        decisions = db.search_decisions(search)
    else:
        # Load all decisions
        decisions = []
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions")
            rows = cursor.fetchall()
            for row in rows:
                import json
                from app.models.decision import Decision
                decisions.append(Decision(
                    decision_id=row["decision_id"],
                    title=row["title"],
                    problem=row["problem"],
                    context=row["context"],
                    constraints=row["constraints"],
                    alternatives=row["alternatives"],
                    decision=row["decision"],
                    reasoning=row["reasoning"],
                    implementation=row["implementation"],
                    outcomes=row["outcomes"],
                    lessons=row["lessons"],
                    confidence=row["confidence"],
                    evidence_ids=json.loads(row["evidence_ids"] or "[]")
                ))
    return [d.to_dict() for d in decisions]


@app.get("/api/decisions/{decision_id}")
async def get_decision_details(decision_id: str):
    """
    Retrieve full details of a specific reconstructed decision with its chronological timeline.
    """
    db = get_db()
    decision = db.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Reconstructed decision not found")
    
    dec_dict = decision.to_dict()
    
    # Load connected artifacts for chronological timeline
    timeline = []
    if decision.evidence_ids:
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query all artifacts matching evidence_ids
            placeholders = ",".join("?" for _ in decision.evidence_ids)
            query = f"SELECT * FROM artifacts WHERE artifact_id IN ({placeholders})"
            cursor.execute(query, decision.evidence_ids)
            rows = cursor.fetchall()
            
            for row in rows:
                import json
                timestamps = json.loads(row["timestamps"] or "{}")
                date_str = timestamps.get("created_at") or timestamps.get("deployed_at") or timestamps.get("committed_at") or timestamps.get("resolved_at") or ""
                
                timeline.append({
                    "artifact_id": row["artifact_id"],
                    "source": row["source"],
                    "source_type": row["source_type"],
                    "external_id": row["external_id"],
                    "title": row["title"],
                    "content": row["content"],
                    "author": row["author"],
                    "timestamp": date_str,
                    "metadata": json.loads(row["metadata"] or "{}"),
                })
                
    # Sort timeline chronologically (ascending date string)
    timeline.sort(key=lambda x: x["timestamp"] or "9999-12-31")
    dec_dict["timeline"] = timeline
    
    return dec_dict


@app.get("/api/query")
async def run_query_agent(q: str = Query(..., description="The natural language question about engineering choices")):
    """
    Query Agent portal returning markdown responses grounded in graphs and databases.
    """
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database not initialized.")
    
    try:
        agent = QueryAgent(db_path=DB_PATH)
        response = agent.query(q)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")


# Serve SPA
@app.get("/")
async def read_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": "static/index.html not created yet. Please create it."}
        )
    return FileResponse(index_path)


# Mount static assets
app.mount("/", StaticFiles(directory="static"), name="static")
