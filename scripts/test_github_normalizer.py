import json
from pathlib import Path

from app.sources.github.normalizer import (
    normalize_issue,
    normalize_pull_request,
    normalize_commit,
    normalize_document,
)


DATASET_PATH = Path("data/raw/github/backstage/backstage")
REPOSITORY = "backstage/backstage"


def print_artifact(label: str, artifact) -> None:
    print(f"\n{'=' * 60}")
    print(label)
    print("=" * 60)

    print(
        json.dumps(
            artifact.model_dump(mode="json"),
            indent=2,
        )
    )


def main() -> None:

    # --------------------------------------------------
    # LOAD RAW DATA
    # --------------------------------------------------

    with (DATASET_PATH / "issues" / "issues.json").open(
        "r", encoding="utf-8",
    ) as file:
        issues = json.load(file)

    with (DATASET_PATH / "pull_requests" / "pull_requests.json").open(
        "r", encoding="utf-8",
    ) as file:
        pull_requests = json.load(file)

    with (DATASET_PATH / "pull_requests" / "commits.json").open(
        "r", encoding="utf-8",
    ) as file:
        pr_commits = json.load(file)

    with (DATASET_PATH / "documents" / "documents.json").open(
        "r", encoding="utf-8",
    ) as file:
        documents = json.load(file)

    # --------------------------------------------------
    # TEST normalize_issue()
    # --------------------------------------------------

    first_issue = issues[0]

    print("\nRAW GITHUB ISSUE")
    print("-" * 60)
    print(f"Number: {first_issue.get('number')}")
    print(f"Title: {first_issue.get('title')}")
    print(f"Author: {(first_issue.get('user') or {}).get('login')}")
    print(f"Created At: {first_issue.get('created_at')}")

    issue_artifact = normalize_issue(
        issue=first_issue,
        repository=REPOSITORY,
    )

    expected_issue_id = (
        f"github:{REPOSITORY}:issue:"
        f"{first_issue['number']}"
    )

    assert issue_artifact.artifact_id == expected_issue_id, (
        f"Issue ID mismatch: {issue_artifact.artifact_id} "
        f"!= {expected_issue_id}"
    )

    assert issue_artifact.source.value == "github"
    assert issue_artifact.source_scope == REPOSITORY
    assert issue_artifact.artifact_type.value == "issue"

    print_artifact("NORMALIZED ISSUE ARTIFACT", issue_artifact)
    print(f"\n[PASS] Issue artifact_id: {issue_artifact.artifact_id}")

    # --------------------------------------------------
    # TEST normalize_pull_request()
    # --------------------------------------------------

    first_pr = pull_requests[0]

    print("\nRAW GITHUB PULL REQUEST")
    print("-" * 60)
    print(f"Number: {first_pr.get('number')}")
    print(f"Title: {first_pr.get('title')}")
    print(f"Author: {(first_pr.get('user') or {}).get('login')}")
    print(f"Merged At: {first_pr.get('merged_at')}")

    pr_artifact = normalize_pull_request(
        pull_request=first_pr,
        repository=REPOSITORY,
    )

    expected_pr_id = (
        f"github:{REPOSITORY}:pull_request:"
        f"{first_pr['number']}"
    )

    assert pr_artifact.artifact_id == expected_pr_id, (
        f"PR ID mismatch: {pr_artifact.artifact_id} "
        f"!= {expected_pr_id}"
    )

    assert pr_artifact.source.value == "github"
    assert pr_artifact.artifact_type.value == "pull_request"

    print_artifact("NORMALIZED PR ARTIFACT", pr_artifact)
    print(f"\n[PASS] PR artifact_id: {pr_artifact.artifact_id}")

    # --------------------------------------------------
    # TEST normalize_commit()
    # --------------------------------------------------

    # Get the first commit from the first PR's commits.
    first_pr_number = str(first_pr["number"])
    first_pr_commits = pr_commits.get(first_pr_number, [])

    if not first_pr_commits:
        # Fallback: use any PR that has commits.
        for pr_num, commits_list in pr_commits.items():
            if commits_list:
                first_pr_number = pr_num
                first_pr_commits = commits_list
                break

    first_commit = first_pr_commits[0]

    commit_data = first_commit.get("commit") or {}
    commit_author = commit_data.get("author") or {}

    print("\nRAW GITHUB COMMIT")
    print("-" * 60)
    print(f"SHA: {first_commit.get('sha')}")
    print(f"Message: {(commit_data.get('message') or '')[:80]}")
    print(f"Author: {(first_commit.get('author') or {}).get('login')}")
    print(f"Date: {commit_author.get('date')}")

    commit_artifact = normalize_commit(
        commit=first_commit,
        repository=REPOSITORY,
    )

    expected_commit_id = (
        f"github:{REPOSITORY}:commit:"
        f"{first_commit['sha']}"
    )

    assert commit_artifact.artifact_id == expected_commit_id, (
        f"Commit ID mismatch: {commit_artifact.artifact_id} "
        f"!= {expected_commit_id}"
    )

    assert commit_artifact.source.value == "github"
    assert commit_artifact.artifact_type.value == "commit"

    print_artifact("NORMALIZED COMMIT ARTIFACT", commit_artifact)
    print(f"\n[PASS] Commit artifact_id: {commit_artifact.artifact_id}")

    # --------------------------------------------------
    # TEST normalize_document()
    # --------------------------------------------------

    first_document = documents[0]

    print("\nRAW GITHUB DOCUMENT")
    print("-" * 60)
    print(f"Path: {first_document.get('path')}")
    print(f"Type: {first_document.get('document_type')}")
    print(f"Size: {first_document.get('size')}")
    content_preview = (first_document.get("content") or "")[:100]
    print(f"Content preview: {content_preview}")

    document_artifact = normalize_document(
        document=first_document,
        repository=REPOSITORY,
    )

    expected_doc_id = (
        f"github:{REPOSITORY}:document:"
        f"{first_document['path']}"
    )

    assert document_artifact.artifact_id == expected_doc_id, (
        f"Document ID mismatch: {document_artifact.artifact_id} "
        f"!= {expected_doc_id}"
    )

    assert document_artifact.source.value == "github"
    assert document_artifact.artifact_type.value == "document"
    assert document_artifact.author is None
    assert document_artifact.created_at is None

    print_artifact("NORMALIZED DOCUMENT ARTIFACT", document_artifact)
    print(f"\n[PASS] Document artifact_id: {document_artifact.artifact_id}")

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ALL NORMALIZER TESTS PASSED")
    print("=" * 60)

    print(f"  [PASS] normalize_issue()        -> {issue_artifact.artifact_id}")
    print(f"  [PASS] normalize_pull_request() -> {pr_artifact.artifact_id}")
    print(f"  [PASS] normalize_commit()       -> {commit_artifact.artifact_id}")
    print(f"  [PASS] normalize_document()     -> {document_artifact.artifact_id}")


if __name__ == "__main__":
    main()