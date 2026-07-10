import json
import re
from typing import Any, Dict, List
from fastapi import APIRouter, Header, Request, HTTPException
from pathlib import Path

from app.models.artifact import Artifact
from app.models.relationship import Relationship
from app.models.decision import Decision
from app.core.memory import DecisionMemory
from app.core.graph import EvidenceGraph
from app.core.llm import LLMProvider
from app.sources.github.normalizer import GitHubNormalizer

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


def process_live_relationships(
    art: Artifact,
    db: DecisionMemory,
    graph: EvidenceGraph,
) -> List[Relationship]:
    """
    Extract relationships for a newly ingested live artifact and save them to database.
    """
    new_rels = []
    text_content = f"{art.title}\n{art.content}"
    
    # 1. Extract ADR references (e.g. "ADR-0023")
    adr_matches = re.findall(r"(adr-\d+)", text_content, re.IGNORECASE)
    for match in set(adr_matches):
        adr_ext_id = match.upper()
        # Find if this ADR exists in database/graph by scanning nodes
        adr_node_id = None
        for n_id, n_data in graph.graph.nodes(data=True):
            if n_data.get("source_type") == "adr" and n_data.get("external_id", "").upper() == adr_ext_id:
                adr_node_id = n_id
                break

        if adr_node_id:
            rel_type = "implements_adr" if art.source_type in ["commit", "pull_request"] else "references_adr"
            rel_id = Relationship.generate_id(art.artifact_id, adr_node_id, rel_type)
            relationship = Relationship(
                relationship_id=rel_id,
                source_id=art.artifact_id,
                target_id=adr_node_id,
                relationship_type=rel_type,
                confidence=1.0,
                reasoning=f"Webhook: Direct reference to {adr_ext_id} parsed in content.",
                provenance={"extractor": "LiveWebhookIngestion", "type": "regex"}
            )
            new_rels.append(relationship)

    # 2. Extract Jira Issue keys (e.g. "AL5-12" or "SS23-9")
    jira_matches = re.findall(r"([A-Z][A-Z0-9]+-\d+)", text_content)
    for match in set(jira_matches):
        # Filter out ADR matches
        if match.startswith("ADR-"):
            continue
        issue_node_id = None
        for n_id, n_data in graph.graph.nodes(data=True):
            if n_data.get("source_type") == "issue" and n_data.get("external_id", "").upper() == match.upper():
                issue_node_id = n_id
                break

        if issue_node_id:
            rel_type = "resolves_issue" if art.source_type == "pull_request" else "relates_to"
            rel_id = Relationship.generate_id(art.artifact_id, issue_node_id, rel_type)
            relationship = Relationship(
                relationship_id=rel_id,
                source_id=art.artifact_id,
                target_id=issue_node_id,
                relationship_type=rel_type,
                confidence=1.0,
                reasoning=f"Webhook: Direct reference to Jira ticket {match} parsed in content.",
                provenance={"extractor": "LiveWebhookIngestion", "type": "regex"}
            )
            new_rels.append(relationship)

    # 3. For commits: link to PR if PR metadata is present
    if art.source_type == "commit" and "pull_request" in art.metadata:
        pr_num = str(art.metadata["pull_request"])
        # Find PR node ID in graph
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("source_type") == "pull_request" and node_data.get("external_id") == pr_num:
                rel_type = "contained_in"
                rel_id = Relationship.generate_id(art.artifact_id, node_id, rel_type)
                relationship = Relationship(
                    relationship_id=rel_id,
                    source_id=art.artifact_id,
                    target_id=node_id,
                    relationship_type=rel_type,
                    confidence=1.0,
                    reasoning=f"Webhook: Commit associated with PR #{pr_num} via webhook metadata.",
                    provenance={"extractor": "LiveWebhookIngestion", "type": "metadata"}
                )
                new_rels.append(relationship)

    if new_rels:
        db.save_relationships_batch(new_rels)
        # Add to graph
        for r in new_rels:
            graph.add_relationship(r)
            
    return new_rels


def incremental_reconstruct_decision(
    adr_id: str,
    db: DecisionMemory,
    graph: EvidenceGraph,
    llm: LLMProvider,
) -> None:
    """
    Reconstruct decision for a single ADR seed in real-time.
    """
    adr = graph.get_artifact(adr_id)
    if not adr:
        return

    # 2-hop traversal in the graph (ultrafast using undirected cache!)
    cluster_ids = graph.get_connected_cluster(adr_id, directed=False, cutoff=2)
    cluster_artifacts = [graph.get_artifact(cid) for cid in cluster_ids if graph.get_artifact(cid)]

    evidence_lines = []
    for art in cluster_artifacts:
        if art.artifact_id == adr_id:
            continue
        evidence_lines.append(
            f"- [{art.source_type.upper()}] {art.external_id}: \"{art.title}\"\n"
            f"  Content: {art.content[:200]}\n"
        )
    cluster_text = "\n".join(evidence_lines)

    try:
        result = llm.reconstruct_decision(
            adr=adr.to_dict(),
            cluster_text=cluster_text,
            connected_artifacts=[a.to_dict() for a in cluster_artifacts if a.artifact_id != adr_id]
        )

        decision_uuid = Decision.generate_id(adr.external_id)
        decision = Decision(
            decision_id=decision_uuid,
            title=result.get("title") or adr.title,
            problem=result.get("problem") or "No problem description.",
            context=result.get("context") or "No context description.",
            constraints=result.get("constraints") or "No constraints.",
            alternatives=result.get("alternatives") or "No alternatives considered.",
            decision=result.get("decision") or "No decision description.",
            reasoning=result.get("reasoning") or "No reasoning provided.",
            implementation=result.get("implementation") or "No implementation details.",
            outcomes=result.get("outcomes") or "No operational outcomes.",
            lessons=result.get("lessons") or "No lessons learned.",
            confidence=float(result.get("confidence", 0.9)),
            evidence_ids=list(cluster_ids)
        )
        db.save_decision(decision)
        print(f"Incremental Update: Reconstructed decision successfully for {adr.external_id}.")
    except Exception as e:
        print(f"Incremental Update ERROR: Failed to reconstruct decision for {adr.external_id}: {e}")


@router.post("/github")
async def github_webhook(request: Request, x_github_event: str = Header(None)):
    """
    GitHub webhook handler for push, pull_request, and issues events.
    """
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    payload = await request.json()
    db = DecisionMemory()
    
    # Initialize graph by loading existing records from SQLite
    graph = EvidenceGraph()
    # Read artifacts and relationships to keep graph representation hot
    # (Since we read from SQLite, this takes less than 0.1s!)
    with sqlite3_connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM artifacts")
        for row in cursor.fetchall():
            graph.add_artifact(Artifact(
                artifact_id=row[0], source=row[1], source_type=row[2], external_id=row[3],
                title=row[4], content=row[5], author=row[6], timestamps=json.loads(row[7] or "{}"),
                url=row[8], context=json.loads(row[9] or "{}"), metadata=json.loads(row[10] or "{}"),
                provenance=json.loads(row[11] or "{}")
            ))
        cursor.execute("SELECT * FROM relationships")
        for row in cursor.fetchall():
            graph.add_relationship(Relationship(
                relationship_id=row[0], source_id=row[1], target_id=row[2], relationship_type=row[3],
                confidence=row[4], reasoning=row[5], evidence=json.loads(row[6] or "{}"),
                provenance=json.loads(row[7] or "{}")
            ))

    llm = LLMProvider()
    normalizer = GitHubNormalizer()

    ingested_artifacts = []
    affected_adrs = set()

    if x_github_event == "push":
        # Process commits in push
        repo_name = payload.get("repository", {}).get("name", "unknown-repo")
        author = payload.get("pusher", {}).get("name", "unknown-author")
        
        for commit in payload.get("commits", []):
            raw_commit = {
                "sha": commit.get("id"),
                "commit": {
                    "author": {"name": commit.get("author", {}).get("name"), "date": commit.get("timestamp")},
                    "message": commit.get("message")
                },
                "html_url": commit.get("url"),
                "repository": repo_name
            }
            art = normalizer.normalize_commit(raw_commit)
            db.save_artifact(art)
            graph.add_artifact(art)
            ingested_artifacts.append(art)
            
            # Extract links
            rels = process_live_relationships(art, db, graph)
            for r in rels:
                if ":adr:" in r.target_id.lower():
                    affected_adrs.add(r.target_id)

    elif x_github_event == "pull_request":
        # Process PR changes
        pr_data = payload.get("pull_request", {})
        repo_name = payload.get("repository", {}).get("name", "unknown-repo")
        
        # We normalize raw PR details
        raw_pr = {
            "number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "body": pr_data.get("body") or "",
            "user": {"login": pr_data.get("user", {}).get("login")},
            "created_at": pr_data.get("created_at"),
            "html_url": pr_data.get("html_url"),
            "base": {"repo": {"name": repo_name}}
        }
        art = normalizer.normalize_pr(raw_pr)
        db.save_artifact(art)
        graph.add_artifact(art)
        ingested_artifacts.append(art)

        # Extract links
        rels = process_live_relationships(art, db, graph)
        for r in rels:
            if ":adr:" in r.target_id.lower():
                affected_adrs.add(r.target_id)

    elif x_github_event == "issues":
        # Process Issue updates
        issue_data = payload.get("issue", {})
        repo_name = payload.get("repository", {}).get("name", "unknown-repo")
        
        raw_issue = {
            "number": issue_data.get("number"),
            "title": issue_data.get("title"),
            "body": issue_data.get("body") or "",
            "user": {"login": issue_data.get("user", {}).get("login")},
            "created_at": issue_data.get("created_at"),
            "html_url": issue_data.get("html_url"),
            "repository": repo_name
        }
        art = normalizer.normalize_issue(raw_issue)
        db.save_artifact(art)
        graph.add_artifact(art)
        ingested_artifacts.append(art)

        # Extract links
        rels = process_live_relationships(art, db, graph)
        for r in rels:
            if ":adr:" in r.target_id.lower():
                affected_adrs.add(r.target_id)

    else:
        return {"status": "ignored", "reason": f"Event type {x_github_event} not handled"}

    # Re-run decision reconstruction for any affected ADR seeds
    for adr_id in affected_adrs:
        incremental_reconstruct_decision(adr_id, db, graph, llm)

    return {
        "status": "success",
        "ingested_count": len(ingested_artifacts),
        "affected_adr_seeds": list(affected_adrs)
    }


def sqlite3_connect(db_path: Path):
    import sqlite3
    return sqlite3.connect(db_path)
