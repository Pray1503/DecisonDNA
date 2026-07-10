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


@app.get("/api/artifacts")
async def list_artifacts(
    source: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List artifacts with optional filters for source, type, author, and keyword search.
    """
    if not DB_PATH.exists():
        return {"artifacts": [], "total": 0}

    try:
        import json as _json
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if source:
            conditions.append("source = ?")
            params.append(source)
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if author:
            conditions.append("author LIKE ?")
            params.append(f"%{author}%")
        if search:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Count total
        cursor.execute(f"SELECT COUNT(*) FROM artifacts {where_clause}", params)
        total = cursor.fetchone()[0]

        # Fetch page
        cursor.execute(
            f"SELECT * FROM artifacts {where_clause} LIMIT ? OFFSET ?",
            params + [limit, offset]
        )
        rows = cursor.fetchall()

        artifacts = []
        for row in rows:
            artifacts.append({
                "artifact_id": row["artifact_id"],
                "source": row["source"],
                "source_type": row["source_type"],
                "external_id": row["external_id"],
                "title": row["title"],
                "content": (row["content"] or "")[:300],
                "author": row["author"],
                "timestamps": _json.loads(row["timestamps"] or "{}"),
                "url": row["url"],
                "context": _json.loads(row["context"] or "{}"),
                "metadata": _json.loads(row["metadata"] or "{}"),
            })

        conn.close()
        return {"artifacts": artifacts, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact_detail(artifact_id: str):
    """
    Retrieve full details of a specific artifact.
    """
    db = get_db()
    art = db.get_artifact(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return art.to_dict()


@app.get("/api/relationships")
async def list_relationships(
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """
    List relationships with optional filters.
    """
    if not DB_PATH.exists():
        return {"relationships": [], "total": 0}

    try:
        import json as _json
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)
        if target_id:
            conditions.append("target_id = ?")
            params.append(target_id)
        if relationship_type:
            conditions.append("relationship_type = ?")
            params.append(relationship_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor.execute(f"SELECT COUNT(*) FROM relationships {where_clause}", params)
        total = cursor.fetchone()[0]

        cursor.execute(
            f"SELECT * FROM relationships {where_clause} LIMIT ?",
            params + [limit]
        )
        rows = cursor.fetchall()

        rels = []
        for row in rows:
            rels.append({
                "relationship_id": row["relationship_id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "relationship_type": row["relationship_type"],
                "confidence": row["confidence"],
                "reasoning": row["reasoning"],
            })

        conn.close()
        return {"relationships": rels, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/graph/summary")
async def get_graph_summary():
    """
    Return graph stats for visualization: node counts by type, edge counts by type, sources.
    """
    if not DB_PATH.exists():
        return {"nodes": {}, "edges": {}, "sources": {}, "total_nodes": 0, "total_edges": 0}

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT source_type, COUNT(*) FROM artifacts GROUP BY source_type")
        nodes_by_type = dict(cursor.fetchall())

        cursor.execute("SELECT source, COUNT(*) FROM artifacts GROUP BY source")
        nodes_by_source = dict(cursor.fetchall())

        cursor.execute("SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type")
        edges_by_type = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(*) FROM artifacts")
        total_nodes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships")
        total_edges = cursor.fetchone()[0]

        # Top connected nodes (most relationships)
        cursor.execute("""
            SELECT id, COUNT(*) as cnt FROM (
                SELECT source_id as id FROM relationships
                UNION ALL
                SELECT target_id as id FROM relationships
            ) GROUP BY id ORDER BY cnt DESC LIMIT 10
        """)
        top_nodes = []
        for row in cursor.fetchall():
            node_id = row[0]
            count = row[1]
            cursor.execute("SELECT title, source_type, source FROM artifacts WHERE artifact_id = ?", (node_id,))
            node_info = cursor.fetchone()
            if node_info:
                top_nodes.append({
                    "artifact_id": node_id,
                    "title": node_info[0],
                    "source_type": node_info[1],
                    "source": node_info[2],
                    "connection_count": count,
                })

        conn.close()

        return {
            "nodes_by_type": nodes_by_type,
            "nodes_by_source": nodes_by_source,
            "edges_by_type": edges_by_type,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "top_connected": top_nodes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/graph/cluster/{artifact_id}")
async def get_graph_cluster(artifact_id: str, hops: int = Query(2, ge=1, le=3)):
    """
    Return the connected cluster around an artifact within N hops.
    """
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database not initialized.")

    try:
        import json as _json
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # BFS traversal to find connected nodes
        visited = set()
        queue = [(artifact_id, 0)]
        visited.add(artifact_id)

        while queue:
            current_id, depth = queue.pop(0)
            if depth >= hops:
                continue

            # Find neighbors via relationships (both directions)
            cursor.execute(
                "SELECT target_id FROM relationships WHERE source_id = ?",
                (current_id,)
            )
            for row in cursor.fetchall():
                if row["target_id"] not in visited:
                    visited.add(row["target_id"])
                    queue.append((row["target_id"], depth + 1))

            cursor.execute(
                "SELECT source_id FROM relationships WHERE target_id = ?",
                (current_id,)
            )
            for row in cursor.fetchall():
                if row["source_id"] not in visited:
                    visited.add(row["source_id"])
                    queue.append((row["source_id"], depth + 1))

        # Fetch node details
        nodes = []
        for node_id in visited:
            cursor.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (node_id,))
            row = cursor.fetchone()
            if row:
                nodes.append({
                    "artifact_id": row["artifact_id"],
                    "source": row["source"],
                    "source_type": row["source_type"],
                    "external_id": row["external_id"],
                    "title": row["title"],
                    "author": row["author"],
                })

        # Fetch edges between cluster nodes
        if visited:
            placeholders = ",".join("?" for _ in visited)
            cursor.execute(
                f"SELECT * FROM relationships WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})",
                list(visited) + list(visited)
            )
            edges = []
            for row in cursor.fetchall():
                edges.append({
                    "source_id": row["source_id"],
                    "target_id": row["target_id"],
                    "relationship_type": row["relationship_type"],
                    "confidence": row["confidence"],
                })

        conn.close()
        return {"nodes": nodes, "edges": edges, "center": artifact_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/activity")
async def get_activity_feed(
    source_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Recent artifacts ordered by timestamp for activity feed.
    """
    if not DB_PATH.exists():
        return {"items": [], "total": 0}

    try:
        import json as _json
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cursor.execute(f"SELECT COUNT(*) FROM artifacts {where_clause}", params)
        total = cursor.fetchone()[0]

        # Order by timestamp extracted from JSON
        cursor.execute(
            f"""SELECT * FROM artifacts {where_clause}
                ORDER BY json_extract(timestamps, '$.created_at') DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset]
        )
        rows = cursor.fetchall()

        items = []
        for row in rows:
            timestamps = _json.loads(row["timestamps"] or "{}")
            ts = timestamps.get("created_at") or timestamps.get("committed_at") or timestamps.get("deployed_at") or ""
            items.append({
                "artifact_id": row["artifact_id"],
                "source": row["source"],
                "source_type": row["source_type"],
                "external_id": row["external_id"],
                "title": row["title"],
                "author": row["author"],
                "timestamp": ts,
                "url": row["url"],
            })

        conn.close()
        return {"items": items, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


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

