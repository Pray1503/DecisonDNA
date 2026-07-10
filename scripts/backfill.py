import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.artifact import Artifact
from app.models.relationship import Relationship
from app.models.decision import Decision
from app.sources.github.normalizer import GitHubNormalizer
from app.sources.jira.client import JiraClient
from app.sources.jira.normalizer import JiraNormalizer
from app.sources.slack.client import SlackClient
from app.sources.slack.normalizer import SlackNormalizer
from app.sources.datadog.client import DatadogClient
from app.sources.datadog.normalizer import DatadogNormalizer
from app.sources.kubernetes.client import KubernetesClient
from app.sources.kubernetes.normalizer import KubernetesNormalizer

from app.core.graph import EvidenceGraph
from app.core.llm import LLMProvider
from app.core.embeddings import EmbeddingService
from app.core.memory import DecisionMemory


def main():
    dataset_dir = Path("D:/dataset generator/OrgMemory-10K")
    db_file = Path("data/decision_memory.db")

    if not dataset_dir.exists():
        print(f"ERROR: Dataset directory {dataset_dir} does not exist.")
        sys.exit(1)

    print("==================================================")
    # --------------------------------------------------
    # 1. INITIALIZE CLIENTS, NORMALIZERS, AND SERVICES
    # --------------------------------------------------
    print("Initializing clients and normalizers...")
    github_norm = GitHubNormalizer()

    jira_client = JiraClient(dataset_dir / "jira" / "jira_tickets.json")
    jira_norm = JiraNormalizer()

    slack_client = SlackClient(dataset_dir / "feedback" / "developer_feedback.json")
    slack_norm = SlackNormalizer()

    datadog_client = DatadogClient(dataset_dir / "incidents" / "incidents.json")
    datadog_norm = DatadogNormalizer()

    k8s_client = KubernetesClient(dataset_dir / "deployments" / "deployments.json")
    k8s_norm = KubernetesNormalizer()

    memory = DecisionMemory(db_path=db_file)
    llm = LLMProvider()
    embedding_service = EmbeddingService()

    # Clear old tables if db exists
    if db_file.exists():
        print("Clearing existing database tables...")
        import sqlite3
        conn = sqlite3.connect(db_file)
        conn.execute("DROP TABLE IF EXISTS artifacts")
        conn.execute("DROP TABLE IF EXISTS relationships")
        conn.execute("DROP TABLE IF EXISTS decisions")
        conn.commit()
        conn.close()
    
    # Reinitialize tables
    memory = DecisionMemory(db_path=db_file)

    # --------------------------------------------------
    # 2. LOAD AND NORMALIZE ALL ARTIFACTS
    # --------------------------------------------------
    print("\n--- Ingesting and Normalizing Artifacts ---")
    artifacts: List[Artifact] = []

    # A. ADRs
    adrs_path = dataset_dir / "architecture" / "adrs.json"
    if adrs_path.exists():
        with open(adrs_path, "r", encoding="utf-8") as f:
            adrs = json.load(f)
            print(f"Normalizing {len(adrs)} ADRs...")
            for adr in adrs:
                artifacts.append(github_norm.normalize_adr(adr, raw_path=str(adrs_path)))

    # B. Commits
    commits_path = dataset_dir / "github" / "commits.json"
    if commits_path.exists():
        with open(commits_path, "r", encoding="utf-8") as f:
            commits = json.load(f)
            print(f"Normalizing {len(commits)} GitHub Commits...")
            for c in commits:
                artifacts.append(github_norm.normalize_commit(c, raw_path=str(commits_path)))

    # C. Pull Requests
    prs_path = dataset_dir / "github" / "pull_requests.json"
    if prs_path.exists():
        with open(prs_path, "r", encoding="utf-8") as f:
            prs = json.load(f)
            print(f"Normalizing {len(prs)} GitHub Pull Requests...")
            for pr in prs:
                artifacts.append(github_norm.normalize_pull_request(pr, raw_path=str(prs_path)))

    # D. Jira Tickets
    tickets = jira_client.get_tickets()
    print(f"Normalizing {len(tickets)} Jira Tickets...")
    for t in tickets:
        artifacts.append(jira_norm.normalize_ticket(t))

    # E. Slack Retro Posts
    slack_msgs = slack_client.get_messages()
    print(f"Normalizing {len(slack_msgs)} Slack Messages...")
    for m in slack_msgs:
        artifacts.append(slack_norm.normalize_message(m))

    # F. Datadog Incidents
    incidents = datadog_client.get_incidents()
    print(f"Normalizing {len(incidents)} Datadog Incidents...")
    for inc in incidents:
        artifacts.append(datadog_norm.normalize_incident(inc))

    # G. Kubernetes Deployments
    deployments = k8s_client.get_deployments()
    print(f"Normalizing {len(deployments)} Kubernetes Deployments...")
    for dep in deployments:
        artifacts.append(k8s_norm.normalize_deployment(dep))

    print(f"Total Normalized Artifacts: {len(artifacts)}")

    # --------------------------------------------------
    # 3. BUILD RESOLUTION INDEXES
    # --------------------------------------------------
    print("\nBuilding indexes for relationship resolution...")
    adr_index: Dict[str, str] = {}      # external_id -> artifact_id
    jira_index: Dict[str, str] = {}     # external_id -> artifact_id
    pr_index: Dict[tuple, str] = {}     # (repository, pr_number) -> artifact_id
    pr_id_index: Dict[tuple, str] = {}  # (repository, pr_id) -> artifact_id
    dep_index: Dict[str, str] = {}      # deployment_id -> artifact_id

    for art in artifacts:
        ext_id = art.external_id
        repo = art.context.get("repository") or art.context.get("repo")
        repo_lower = str(repo).strip().lower() if repo else ""

        if art.source_type == "adr":
            adr_index[ext_id] = art.artifact_id
        elif art.source_type == "issue" and art.source == "jira":
            jira_index[ext_id] = art.artifact_id
        elif art.source_type == "pull_request":
            if repo_lower:
                pr_index[(repo_lower, ext_id.lower())] = art.artifact_id
                pr_id = art.metadata.get("pr_id")
                if pr_id:
                    pr_id_index[(repo_lower, str(pr_id).strip().lower())] = art.artifact_id
        elif art.source_type == "deployment":
            dep_index[ext_id] = art.artifact_id

    # --------------------------------------------------
    # 4. EXTRACT DETERMINISTIC RELATIONSHIPS
    # --------------------------------------------------
    print("\n--- Extracting Deterministic Relationships ---")
    relationships: Dict[str, Relationship] = {}
    provenance = {"extracted_at": "now", "extractor": "BatchBackfillWorker", "version": "1.0.0"}

    for art in artifacts:
        art_id = art.artifact_id
        repo = art.context.get("repository") or art.context.get("repo")
        repo_lower = str(repo).strip().lower() if repo else ""

        # A. Pull Requests
        if art.source_type == "pull_request":
            jira_ticket = art.metadata.get("jira_ticket")
            if jira_ticket:
                target_id = jira_index.get(jira_ticket)
                if target_id:
                    rel_type = "resolves_issue"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="PR metadata links JIRA issue.", provenance=provenance
                    )
            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="PR metadata links ADR.", provenance=provenance
                    )

        # B. Commits
        elif art.source_type == "commit":
            pr_id = art.metadata.get("pull_request")
            if pr_id and repo_lower:
                pr_art_id = pr_index.get((repo_lower, pr_id.lower()))
                if pr_art_id:
                    rel_type = "contains_commit"
                    rel_id = Relationship.generate_id(pr_art_id, art_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=pr_art_id, target_id=art_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="PR contains Commit.", provenance=provenance
                    )
            jira_ticket = art.metadata.get("jira_ticket")
            if jira_ticket:
                target_id = jira_index.get(jira_ticket)
                if target_id:
                    rel_type = "references_issue"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Commit message references JIRA issue.", provenance=provenance
                    )
            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Commit message references ADR.", provenance=provenance
                    )

        # C. Jira Issues dependencies
        elif art.source_type == "issue" and art.source == "jira":
            deps = art.metadata.get("dependencies") or []
            for dep in deps:
                target_id = jira_index.get(dep)
                if target_id:
                    rel_type = "depends_on"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="JIRA ticket dependency.", provenance=provenance
                    )
            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="JIRA ticket implements ADR.", provenance=provenance
                    )

        # D. Slack Retro Messages
        elif art.source_type == "chat" and art.source == "slack":
            adr_id = art.metadata.get("referenced_adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "references_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Slack feedback explicitly mentions ADR.", provenance=provenance
                    )
            # Text matching regex for other ADR mentions
            text_content = art.content
            adr_matches = re.findall(r"(adr-\d+)", text_content, re.IGNORECASE)
            for m in set(adr_matches):
                target_id = adr_index.get(m.upper())
                if target_id:
                    rel_type = "references_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning=f"Slack feedback parses reference to {m.upper()}.", provenance=provenance
                    )

        # E. Datadog Incidents
        elif art.source_type == "incident" and art.source == "datadog":
            linked_dep = art.metadata.get("linked_deployment")
            if linked_dep:
                target_id = dep_index.get(linked_dep)
                if target_id:
                    rel_type = "caused_by_deployment"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Incident caused by deployment rollouts.", provenance=provenance
                    )
            linked_pr = art.metadata.get("linked_pr")
            if linked_pr and repo_lower:
                target_id = pr_id_index.get((repo_lower, linked_pr.lower()))
                if target_id:
                    rel_type = "linked_pr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Incident linked to PR code changes.", provenance=provenance
                    )
            linked_adr = art.metadata.get("linked_adr")
            if linked_adr:
                target_id = adr_index.get(linked_adr)
                if target_id:
                    rel_type = "linked_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Incident post-mortem explicitly links ADR.", provenance=provenance
                    )

        # F. Kubernetes Deployments
        elif art.source_type == "deployment" and art.source == "kubernetes":
            linked_pr = art.metadata.get("linked_pr")
            if linked_pr and repo_lower:
                target_id = pr_id_index.get((repo_lower, linked_pr.lower()))
                if target_id:
                    rel_type = "deploys_pr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Deployment pipeline deploys PR.", provenance=provenance
                    )
            linked_adr = art.metadata.get("linked_adr")
            if linked_adr:
                target_id = adr_index.get(linked_adr)
                if target_id:
                    rel_type = "deploys_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id, source_id=art_id, target_id=target_id,
                        relationship_type=rel_type, confidence=1.0, reasoning="Deployment implements ADR decision release.", provenance=provenance
                    )

    print(f"Total Deterministic Relationships: {len(relationships)}")

    # --------------------------------------------------
    # 5. SEMANTIC PIPELINE MATCHING
    # --------------------------------------------------
    print("\n--- Running AI Semantic Analysis ---")
    # Group artifacts by project scope
    project_groups: Dict[str, Dict[str, List[Any]]] = {}
    for art in artifacts:
        proj = art.context.get("project") or art.context.get("repository") or art.context.get("repo")
        if not proj:
            continue
        proj_key = str(proj).strip().upper()
        if proj_key not in project_groups:
            project_groups[proj_key] = {"adrs": [], "targets": []}

        if art.source_type == "adr":
            project_groups[proj_key]["adrs"].append(art)
        elif art.source_type in ["issue", "pull_request"]:
            project_groups[proj_key]["targets"].append(art)

    SIM_THRESHOLD = 0.45
    candidates: List[Tuple[Any, Any, float]] = []

    for proj_key, group in project_groups.items():
        adrs = group["adrs"]
        targets = group["targets"]
        if not adrs or not targets:
            continue

        adr_texts = [f"Title: {a.title}\nContent: {a.content[:300]}" for a in adrs]
        target_texts = [f"Title: {t.title}\nContent: {t.content[:300]}" for t in targets]

        sim_matrix = embedding_service.calculate_similarities(adr_texts, target_texts)

        for i, adr in enumerate(adrs):
            for j, target in enumerate(targets):
                score = float(sim_matrix[i, j])
                if score >= SIM_THRESHOLD:
                    candidates.append((adr, target, score))

    candidates.sort(key=lambda x: x[2], reverse=True)
    print(f"Found {len(candidates)} semantic similarity pairs above {SIM_THRESHOLD}.")

    # Limit to top 20 new semantic links to save time
    semantic_count = 0
    for adr, target, score in candidates[:20]:
        rel_type = "semantically_related"
        rel_id = Relationship.generate_id(adr.artifact_id, target.artifact_id, rel_type)
        if rel_id not in relationships:
            relationships[rel_id] = Relationship(
                relationship_id=rel_id,
                source_id=adr.artifact_id,
                target_id=target.artifact_id,
                relationship_type=rel_type,
                confidence=score,
                reasoning="Calculated semantic vector cosine similarity matches.",
                evidence={"similarity_score": score},
                provenance=provenance
            )
            semantic_count += 1
    print(f"Added {semantic_count} new semantic relationships.")

    # --------------------------------------------------
    # 6. INITIALIZE EVIDENCE GRAPH AND SAVE TO SQLITE
    # --------------------------------------------------
    print("\n--- Populating SQLite database ---")
    # Build NetworkX graph locally to help with decision local cluster reconstruction
    eg = EvidenceGraph()
    for art in artifacts:
        eg.add_artifact(art)
    for rel in relationships.values():
        eg.add_relationship(rel)

    # Save batches
    memory.save_artifacts_batch(artifacts)
    memory.save_relationships_batch(list(relationships.values()))
    print(f"Artifacts and Relationships tables populated.")

    # --------------------------------------------------
    # 7. STRUCTURED DECISION RECONSTRUCTION (500 SEEDS)
    # --------------------------------------------------
    print("\n--- Reconstructing Structured Decisions (500 Seeds) ---")
    adr_nodes = [node_id for node_id, art in eg.artifacts.items() if art.source_type == "adr"]
    
    decisions_to_save: List[Decision] = []

    # Limit printing to every 50 ADRs to avoid massive CLI log flood
    for idx, adr_id in enumerate(adr_nodes, 1):
        adr = eg.get_artifact(adr_id)
        if not adr:
            continue

        if idx % 50 == 0 or idx == 1 or idx == len(adr_nodes):
            print(f"  - Reconstructing [{idx}/{len(adr_nodes)}] decision for seed {adr.external_id}...")

        # Undirected depth-limited cluster traversal
        cluster_ids = eg.get_connected_cluster(adr_id, directed=False, cutoff=2)
        cluster_artifacts = [eg.get_artifact(cid) for cid in cluster_ids if eg.get_artifact(cid)]

        evidence_lines = []
        for art in cluster_artifacts:
            if art.artifact_id == adr_id:
                continue
            evidence_lines.append(
                f"- [{art.source_type.upper()}] {art.external_id}: \"{art.title}\"\n"
                f"  Content: {art.content[:150].replace('\n', ' ')}...\n"
            )
        cluster_text = "\n".join(evidence_lines)

        result = llm.reconstruct_decision(
            adr=adr.to_dict(),
            cluster_text=cluster_text,
            connected_artifacts=[a.to_dict() for a in cluster_artifacts if a.artifact_id != adr_id]
        )

        decision_uuid = Decision.generate_id(adr.external_id)
        
        # Check if there are incidents or deployments in this cluster
        incidents_in_cluster = [a.external_id for a in cluster_artifacts if a.source_type == "incident"]
        deployments_in_cluster = [a.external_id for a in cluster_artifacts if a.source_type == "deployment"]
        
        outcomes_text = result.get("outcomes") or "Stable rollout."
        if incidents_in_cluster:
            outcomes_text = f"Caused incidents: {', '.join(incidents_in_cluster)}. Deployed in: {', '.join(deployments_in_cluster or [])}."

        decision = Decision(
            decision_id=decision_uuid,
            title=result.get("title") or adr.title,
            problem=result.get("problem") or "No problem statement.",
            context=result.get("context") or "No context.",
            constraints=result.get("constraints") or "No constraints.",
            alternatives=result.get("alternatives") or "No alternatives.",
            decision=result.get("decision") or "No decision.",
            reasoning=result.get("reasoning") or "No reasoning.",
            implementation=result.get("implementation") or "No implementation.",
            outcomes=outcomes_text,
            lessons=result.get("lessons") or "No lessons.",
            confidence=float(result.get("confidence", 0.95)),
            evidence_ids=list(cluster_ids)
        )
        decisions_to_save.append(decision)

    print(f"Saving {len(decisions_to_save)} reconstructed decisions in a single SQLite transaction...")
    memory.save_decisions_batch(decisions_to_save)

    # --------------------------------------------------
    # 8. PRINT SUMMARY REPORT
    # --------------------------------------------------
    print("\n==================================================")
    print("UNIFIED BACKFILL INGESTION RUN COMPLETE!")
    print(f"  - SQLite Database: {db_file}")
    
    # Query final counts directly from sqlite
    import sqlite3
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artifacts")
    art_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relationships")
    rel_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM decisions")
    dec_count = cursor.fetchone()[0]
    
    # Print counts by type
    print(f"  - Saved Artifacts: {art_count}")
    cursor.execute("SELECT source_type, COUNT(*) FROM artifacts GROUP BY source_type")
    for row in cursor.fetchall():
        print(f"    * {row[0].upper()}: {row[1]}")
        
    print(f"  - Saved Relationships: {rel_count}")
    cursor.execute("SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type")
    for row in cursor.fetchall():
        print(f"    * {row[0]}: {row[1]}")
        
    print(f"  - Reconstructed Decisions: {dec_count}")
    conn.close()
    print("==================================================")


if __name__ == "__main__":
    main()
