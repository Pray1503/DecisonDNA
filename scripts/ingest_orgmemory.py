import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.artifact import Artifact
from app.sources.github.normalizer import GitHubNormalizer


def load_json_file(path: Path) -> Any:
    print(f"Loading {path.name}...")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_jira_ticket(ticket: Dict[str, Any]) -> Artifact:
    """
    JIRA normalizer to represent JIRA tickets as universal Issue artifacts.
    """
    ticket_id = str(ticket.get("ticket_id") or "")
    if not ticket_id:
        raise ValueError("JIRA ticket must have a ticket_id")

    title = ticket.get("title") or f"Jira Ticket {ticket_id}"
    content = ticket.get("description") or ""
    author = ticket.get("owner") or "unknown"
    project = ticket.get("project")

    timestamps = {}
    if ticket.get("created_date"):
        timestamps["created_at"] = ticket["created_date"]
    if ticket.get("resolved_date"):
        timestamps["resolved_at"] = ticket["resolved_date"]

    context = {}
    if project:
        context["project"] = project

    # Build structured metadata
    metadata = {
        "ticket_type": ticket.get("type"),
        "status": ticket.get("status"),
        "sprint": ticket.get("sprint"),
        "priority": ticket.get("priority"),
        "dependencies": ticket.get("dependencies") or [],
        "adr": ticket.get("adr"),
    }

    artifact_id = Artifact.generate_id(
        source="jira",
        source_type="issue",
        external_id=ticket_id,
        context=context,
    )

    provenance = {
        "imported_at": "now",
        "normalizer": "JiraNormalizer",
        "version": "1.0.0",
    }

    return Artifact(
        artifact_id=artifact_id,
        source="jira",
        source_type="issue",
        external_id=ticket_id,
        title=title,
        content=content,
        author=author,
        timestamps=timestamps,
        context=context,
        metadata=metadata,
        provenance=provenance,
    )


def main():
    # --------------------------------------------------
    # PATHS CONFIGURATION
    # --------------------------------------------------
    dataset_dir = Path("D:/dataset generator/OrgMemory-10K")
    output_dir = Path("data/normalized")
    output_file = output_dir / "artifacts.jsonl"

    if not dataset_dir.exists():
        print(f"ERROR: Dataset directory {dataset_dir} does not exist.")
        sys.exit(1)

    print(f"Ingesting dataset from: {dataset_dir}")
    print(f"Outputting normalized artifacts to: {output_file}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize normalizers
    github_normalizer = GitHubNormalizer()

    total_normalized = 0

    # Open output file in write mode
    with open(output_file, "w", encoding="utf-8") as out:

        # --------------------------------------------------
        # 1. ARCHITECTURE DECISION RECORDS (ADRs)
        # --------------------------------------------------
        adrs_path = dataset_dir / "architecture" / "adrs.json"
        if adrs_path.exists():
            adrs = load_json_file(adrs_path)
            print(f"Normalizing {len(adrs)} ADRs...")
            adr_count = 0
            for adr in adrs:
                try:
                    artifact = github_normalizer.normalize_adr(
                        raw_adr=adr,
                        raw_path=str(adrs_path)
                    )
                    out.write(json.dumps(artifact.to_dict(), ensure_ascii=False) + "\n")
                    adr_count += 1
                except Exception as e:
                    print(f"Failed to normalize ADR {adr.get('adr_id')}: {e}")
            print(f"Normalized {adr_count} ADRs.")
            total_normalized += adr_count
        else:
            print("WARNING: adrs.json not found in dataset architecture directory.")

        # --------------------------------------------------
        # 2. GITHUB PULL REQUESTS
        # --------------------------------------------------
        prs_path = dataset_dir / "github" / "pull_requests.json"
        if prs_path.exists():
            prs = load_json_file(prs_path)
            print(f"Normalizing {len(prs)} Pull Requests...")
            pr_count = 0
            for pr in prs:
                try:
                    artifact = github_normalizer.normalize_pull_request(
                        raw_pr=pr,
                        raw_path=str(prs_path)
                    )
                    out.write(json.dumps(artifact.to_dict(), ensure_ascii=False) + "\n")
                    pr_count += 1
                except Exception as e:
                    print(f"Failed to normalize PR {pr.get('pr_id')}: {e}")
            print(f"Normalized {pr_count} Pull Requests.")
            total_normalized += pr_count
        else:
            print("WARNING: pull_requests.json not found in dataset github directory.")

        # --------------------------------------------------
        # 3. GITHUB COMMITS
        # --------------------------------------------------
        commits_path = dataset_dir / "github" / "commits.json"
        if commits_path.exists():
            commits = load_json_file(commits_path)
            print(f"Normalizing {len(commits)} Commits...")
            commit_count = 0
            for commit in commits:
                try:
                    artifact = github_normalizer.normalize_commit(
                        raw_commit=commit,
                        raw_path=str(commits_path)
                    )
                    out.write(json.dumps(artifact.to_dict(), ensure_ascii=False) + "\n")
                    commit_count += 1
                except Exception as e:
                    print(f"Failed to normalize Commit {commit.get('commit_sha')}: {e}")
            print(f"Normalized {commit_count} Commits.")
            total_normalized += commit_count
        else:
            print("WARNING: commits.json not found in dataset github directory.")

        # --------------------------------------------------
        # 4. JIRA TICKETS
        # --------------------------------------------------
        jira_path = dataset_dir / "jira" / "jira_tickets.json"
        if jira_path.exists():
            tickets = load_json_file(jira_path)
            print(f"Normalizing {len(tickets)} Jira Tickets...")
            jira_count = 0
            for ticket in tickets:
                try:
                    artifact = normalize_jira_ticket(ticket)
                    out.write(json.dumps(artifact.to_dict(), ensure_ascii=False) + "\n")
                    jira_count += 1
                except Exception as e:
                    print(f"Failed to normalize Jira Ticket {ticket.get('ticket_id')}: {e}")
            print(f"Normalized {jira_count} Jira Tickets.")
            total_normalized += jira_count
        else:
            print("WARNING: jira_tickets.json not found in dataset jira directory.")

    print("\n--------------------------------------------------")
    print(f"INGESTION COMPLETE! Total artifacts normalized: {total_normalized}")
    print(f"Normalized database saved in {output_file}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
