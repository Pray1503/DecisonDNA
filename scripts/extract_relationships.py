import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.artifact import Artifact
from app.models.relationship import Relationship


def main():
    # Paths
    artifacts_file = Path("data/normalized/artifacts.jsonl")
    output_file = Path("data/normalized/relationships.jsonl")

    if not artifacts_file.exists():
        print(f"ERROR: Normalized artifacts file {artifacts_file} does not exist. Run ingestion first.")
        sys.exit(1)

    print(f"Reading artifacts from: {artifacts_file}")
    print(f"Outputting relationships to: {output_file}")

    # Load artifacts into memory
    artifacts: List[Artifact] = []
    with open(artifacts_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            artifacts.append(Artifact.from_dict(json.loads(line)))

    print(f"Loaded {len(artifacts)} artifacts.")

    # --------------------------------------------------
    # BUILD RESOLUTION INDEXES
    # --------------------------------------------------
    print("Building indexes for relationship resolution...")
    
    adr_index: Dict[str, str] = {}      # external_id -> artifact_id
    jira_index: Dict[str, str] = {}     # external_id -> artifact_id
    pr_index: Dict[tuple, str] = {}     # (repository_lower, pr_id_lower) -> artifact_id

    for art in artifacts:
        ext_id = art.external_id
        repo = art.context.get("repository") or art.context.get("repo")
        repo_lower = str(repo).strip().lower() if repo else ""

        if art.source_type == "adr":
            # Map e.g. "ADR-0001" to github:prj-006:adr:ADR-0001
            adr_index[ext_id] = art.artifact_id
            
        elif art.source_type == "issue" and art.source == "jira":
            # Map e.g. "AL5-1" to jira:issue:AL5-1
            jira_index[ext_id] = art.artifact_id
            
        elif art.source_type == "pull_request":
            if repo_lower:
                # Map (repository, external_id) e.g. ("atlaspay-backend", "1")
                pr_index[(repo_lower, ext_id.lower())] = art.artifact_id
                
                # ALSO map (repository, pr_id) from metadata if it exists, e.g. ("atlaspay-backend", "pr-0001")
                pr_id = art.metadata.get("pr_id")
                if pr_id:
                    pr_index[(repo_lower, str(pr_id).strip().lower())] = art.artifact_id

    print(f"Indices built: {len(adr_index)} ADRs, {len(jira_index)} Jira Tickets, {len(pr_index)} Pull Requests.")

    # --------------------------------------------------
    # EXTRACT RELATIONSHIPS
    # --------------------------------------------------
    print("Extracting relationships...")
    relationships: Dict[str, Relationship] = {}  # relationship_id -> Relationship

    provenance = {
        "extracted_at": "now",
        "extractor": "RelationshipExtractor",
        "version": "1.0.0",
    }

    for art in artifacts:
        art_id = art.artifact_id
        repo = art.context.get("repository") or art.context.get("repo")
        repo_lower = str(repo).strip().lower() if repo else ""

        # --- PULL REQUEST RELATIONSHIPS ---
        if art.source_type == "pull_request":
            jira_ticket = art.metadata.get("jira_ticket")
            if jira_ticket:
                target_id = jira_index.get(jira_ticket)
                if target_id:
                    rel_type = "resolves_issue"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=art_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Pull Request metadata explicitly links Jira ticket {jira_ticket}.",
                        evidence={"jira_ticket": jira_ticket},
                        provenance=provenance,
                    )

            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=art_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Pull Request metadata explicitly links ADR {adr_id}.",
                        evidence={"adr": adr_id},
                        provenance=provenance,
                    )

        # --- COMMIT RELATIONSHIPS ---
        elif art.source_type == "commit":
            pr_id = art.metadata.get("pull_request")
            if pr_id and repo_lower:
                # PRs are repository-scoped
                pr_art_id = pr_index.get((repo_lower, pr_id.lower()))
                if pr_art_id:
                    rel_type = "contains_commit"
                    # Edge goes from PR -> Commit
                    rel_id = Relationship.generate_id(pr_art_id, art_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=pr_art_id,
                        target_id=art_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Commit associated with Pull Request {pr_id} in {repo}.",
                        evidence={"pull_request": pr_id, "repository": repo},
                        provenance=provenance,
                    )

            jira_ticket = art.metadata.get("jira_ticket")
            if jira_ticket:
                target_id = jira_index.get(jira_ticket)
                if target_id:
                    rel_type = "references_issue"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=art_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Commit message explicitly references Jira ticket {jira_ticket}.",
                        evidence={"jira_ticket": jira_ticket},
                        provenance=provenance,
                    )

            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=art_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Commit message explicitly references ADR {adr_id}.",
                        evidence={"adr": adr_id},
                        provenance=provenance,
                    )

        # --- JIRA ISSUE RELATIONSHIPS ---
        elif art.source_type == "issue" and art.source == "jira":
            deps = art.metadata.get("dependencies")
            if deps:
                for dep in deps:
                    target_id = jira_index.get(dep)
                    if target_id:
                        rel_type = "depends_on"
                        rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                        relationships[rel_id] = Relationship(
                            relationship_id=rel_id,
                            source_id=art_id,
                            target_id=target_id,
                            relationship_type=rel_type,
                            confidence=1.0,
                            reasoning=f"Jira issue dependency defined: {art.external_id} depends on {dep}.",
                            evidence={"dependency": dep},
                            provenance=provenance,
                        )

            adr_id = art.metadata.get("adr")
            if adr_id:
                target_id = adr_index.get(adr_id)
                if target_id:
                    rel_type = "implements_adr"
                    rel_id = Relationship.generate_id(art_id, target_id, rel_type)
                    relationships[rel_id] = Relationship(
                        relationship_id=rel_id,
                        source_id=art_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=1.0,
                        reasoning=f"Jira ticket metadata references ADR {adr_id}.",
                        evidence={"adr": adr_id},
                        provenance=provenance,
                    )

    # --------------------------------------------------
    # SAVE RELATIONSHIPS
    # --------------------------------------------------
    print(f"Writing {len(relationships)} resolved relationships...")
    
    # Ensure directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Group statistics
    stats: Dict[str, int] = {}

    with open(output_file, "w", encoding="utf-8") as out:
        for rel in relationships.values():
            stats[rel.relationship_type] = stats.get(rel.relationship_type, 0) + 1
            out.write(json.dumps(rel.to_dict(), ensure_ascii=False) + "\n")

    print("\n--------------------------------------------------")
    print(f"EXTRACTION COMPLETE! Total relationships resolved: {len(relationships)}")
    print("Breakdown by type:")
    for rtype, count in stats.items():
        print(f"  - {rtype}: {count}")
    print(f"Relationship database saved in {output_file}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
