import json
from app.sources.github.normalizer import GitHubNormalizer
from app.models.artifact import Artifact


def test_issue_normalization():
    print("\n--- Testing GitHub Issue Normalization ---")
    mock_issue = {
        "number": 42,
        "title": "Fix memory leak in background worker",
        "body": "We observed a growing memory footprint when processing queue messages.",
        "state": "closed",
        "user": {"login": "johndoe"},
        "created_at": "2026-07-01T10:00:00Z",
        "updated_at": "2026-07-02T12:00:00Z",
        "closed_at": "2026-07-02T12:00:00Z",
        "html_url": "https://github.com/backstage/backstage/issues/42",
        "comments": 2,
        "labels": [{"name": "bug"}, {"name": "high-priority"}],
    }

    mock_comments = [
        {
            "user": {"login": "janedoe"},
            "created_at": "2026-07-01T11:00:00Z",
            "body": "I suspect it might be the connection pool not closing connections.",
        },
        {
            "user": {"login": "johndoe"},
            "created_at": "2026-07-02T09:00:00Z",
            "body": "Confirmed. I submitted a PR to patch this.",
        },
    ]

    normalizer = GitHubNormalizer(default_context={"repo": "backstage/backstage"})
    artifact = normalizer.normalize_issue(mock_issue, mock_comments)

    assert isinstance(artifact, Artifact)
    assert artifact.artifact_id == "github:backstage/backstage:issue:42"
    assert artifact.source == "github"
    assert artifact.source_type == "issue"
    assert artifact.external_id == "42"
    assert artifact.title == "Fix memory leak in background worker"
    assert "memory footprint" in artifact.content
    assert "connection pool" in artifact.content
    assert artifact.author == "johndoe"
    assert artifact.timestamps["created_at"] == "2026-07-01T10:00:00Z"
    assert artifact.url == "https://github.com/backstage/backstage/issues/42"
    assert artifact.context["repository"] == "backstage/backstage"
    assert "bug" in artifact.metadata["labels"]
    assert artifact.metadata["state"] == "closed"
    assert len(artifact.metadata["comments"]) == 2

    print("SUCCESS: Issue normalization verified.")
    print(json.dumps(artifact.to_dict(), indent=2))


def test_pr_normalization():
    print("\n--- Testing GitHub PR Normalization ---")
    mock_pr = {
        "number": 101,
        "title": "Resolve AL5-12: Implement connection pool limits",
        "body": "This limits pool sizing to 10 connections.",
        "state": "closed",
        "author": "rickydavis-nt",
        "created_at": "2026-07-02T12:00:00Z",
        "merged_at": "2026-07-03T15:00:00Z",
        "html_url": "https://github.com/backstage/backstage/pull/101",
        "labels": ["enhancement"],
        "adr": "ADR-0012",
    }

    mock_commits = [
        {
            "sha": "abc123xyz456",
            "message": "feat: init pool manager",
            "author": "rickydavis-nt",
        }
    ]

    mock_comments = [
        {
            "author": "reviewer-alice",
            "date": "2026-07-02T14:00:00Z",
            "body": "Looks solid. Merge when ready.",
        }
    ]

    normalizer = GitHubNormalizer()
    context = {"repository": "backstage/backstage"}
    artifact = normalizer.normalize_pull_request(
        mock_pr, mock_comments, mock_commits, context=context
    )

    assert isinstance(artifact, Artifact)
    assert artifact.artifact_id == "github:backstage/backstage:pull_request:101"
    assert artifact.source == "github"
    assert artifact.source_type == "pull_request"
    assert artifact.external_id == "101"
    assert artifact.title == "Resolve AL5-12: Implement connection pool limits"
    assert "pool sizing to 10" in artifact.content
    assert "init pool manager" in artifact.content
    assert "Merge when ready" in artifact.content
    assert artifact.author == "rickydavis-nt"
    assert artifact.timestamps["merged_at"] == "2026-07-03T15:00:00Z"
    assert artifact.metadata["jira_ticket"] == "AL5-12"
    assert artifact.metadata["adr"] == "ADR-0012"
    assert artifact.metadata["merged"] is True

    print("SUCCESS: PR normalization verified.")
    print(json.dumps(artifact.to_dict(), indent=2))


def test_commit_normalization():
    print("\n--- Testing GitHub Commit Normalization ---")
    mock_commit = {
        "sha": "9f304dcbbfbe6f37f5ae57f2f24b8d27e0be245f",
        "author": "lindsaymartinez-nt",
        "message": "feat(atlaspay-ledger): implement decision from ADR-0001 - step 2\n\nResolves AL5-1.",
        "date": "2020-12-30 09:00:00",
        "repository": "atlaspay-backend",
        "parents": ["c27f6a364ab7d43a7a34a0aa38d016d87a1b041e"],
    }

    normalizer = GitHubNormalizer()
    artifact = normalizer.normalize_commit(mock_commit)

    assert isinstance(artifact, Artifact)
    assert artifact.artifact_id == "github:atlaspay-backend:commit:9f304dcbbfbe6f37f5ae57f2f24b8d27e0be245f"
    assert artifact.source == "github"
    assert artifact.source_type == "commit"
    assert artifact.external_id == "9f304dcbbfbe6f37f5ae57f2f24b8d27e0be245f"
    assert artifact.title == "feat(atlaspay-ledger): implement decision from ADR-0001 - step 2"
    assert "Resolves AL5-1." in artifact.content
    assert artifact.author == "lindsaymartinez-nt"
    assert artifact.timestamps["committed_at"] == "2020-12-30 09:00:00"
    assert artifact.metadata["jira_ticket"] == "AL5-1"
    assert artifact.metadata["adr"] == "ADR-0001"
    assert artifact.metadata["parents"] == ["c27f6a364ab7d43a7a34a0aa38d016d87a1b041e"]

    print("SUCCESS: Commit normalization verified.")
    print(json.dumps(artifact.to_dict(), indent=2))


def test_adr_normalization():
    print("\n--- Testing GitHub ADR Normalization ---")
    mock_adr = {
        "adr_id": "ADR-0001",
        "title": "Introduce AWS SQS for decoupled communications in atlaspay-ledger",
        "status": "Accepted",
        "date": "2021-01-12",
        "context": "Direct HTTP calls between services create hard dependencies.",
        "problem": "Tight coupling leads to cascading failures.",
        "alternatives": "1. Keep synchronous REST APIs.\n2. Introduce SQS.",
        "decision": "Integrate AWS SQS.",
        "reason": "Queue tasks and process asynchronously.",
        "consequences": "Requires handling out-of-order execution.",
        "expected_benefits": "Cascading failures avoided.",
        "potential_risks": "Single point of failure.",
        "related_project": "PRJ-006",
        "owner": "EMP-185",
        "tags": ["message-queue", "architecture"],
        "complexity": "Medium",
        "priority": "Low",
        "linked_jira_tickets": ["AL5-1", "AL5-2"],
        "linked_pull_requests": ["PR-0001"],
        "outcome": "Deployed in DEP-0041.",
    }

    normalizer = GitHubNormalizer()
    artifact = normalizer.normalize_adr(mock_adr)

    assert isinstance(artifact, Artifact)
    assert artifact.artifact_id == "github:prj-006:adr:ADR-0001"
    assert artifact.source == "github"
    assert artifact.source_type == "adr"
    assert artifact.external_id == "ADR-0001"
    assert artifact.title == "Introduce AWS SQS for decoupled communications in atlaspay-ledger"
    assert "Integrate AWS SQS." in artifact.content
    assert "Direct HTTP calls" in artifact.content
    assert artifact.author == "EMP-185"
    assert artifact.timestamps["created_at"] == "2021-01-12"
    assert artifact.metadata["status"] == "Accepted"
    assert "message-queue" in artifact.metadata["tags"]
    assert "AL5-1" in artifact.metadata["linked_jira_tickets"]

    print("SUCCESS: ADR normalization verified.")
    print(json.dumps(artifact.to_dict(), indent=2))


if __name__ == "__main__":
    test_issue_normalization()
    test_pr_normalization()
    test_commit_normalization()
    test_adr_normalization()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
