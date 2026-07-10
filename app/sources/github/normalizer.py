from typing import Any

from app.models.artifacts import (
    Artifact,
    ArtifactType,
    Provenance,
    Source,
)


def normalize_issue(
    issue: dict[str, Any],
    repository: str,
) -> Artifact:
    """
    Convert one raw GitHub Issue into a universal Artifact.
    """

    issue_number = str(issue["number"])

    user = issue.get("user") or {}
    author = user.get("login")

    labels = [
        label.get("name")
        for label in issue.get("labels", [])
        if label.get("name")
    ]

    return Artifact(
        source=Source.GITHUB,
        source_scope=repository,
        artifact_type=ArtifactType.ISSUE,
        external_id=issue_number,

        title=issue.get("title"),
        content=issue.get("body"),
        author=author,

        created_at=issue.get("created_at"),
        updated_at=issue.get("updated_at"),

        url=issue.get("html_url"),

        context={
            "repository": repository,
        },

        metadata={
            "state": issue.get("state"),
            "state_reason": issue.get("state_reason"),
            "labels": labels,
            "locked": issue.get("locked"),
            "comments_count": issue.get("comments"),
        },

        provenance=Provenance(
            collector="github_rest_api",
            raw_reference=f"issues/issues.json#{issue_number}",
        ),
    )

def normalize_pull_request(
    pull_request: dict[str, Any],
    repository: str,
) -> Artifact:
    """
    Convert one raw GitHub Pull Request into a universal Artifact.
    """

    pull_number = str(pull_request["number"])

    user = pull_request.get("user") or {}
    author = user.get("login")

    labels = [
        label.get("name")
        for label in pull_request.get("labels", [])
        if label.get("name")
    ]

    base = pull_request.get("base") or {}
    head = pull_request.get("head") or {}

    base_repo = base.get("repo") or {}
    head_repo = head.get("repo") or {}

    return Artifact(
        source=Source.GITHUB,
        source_scope=repository,
        artifact_type=ArtifactType.PULL_REQUEST,
        external_id=pull_number,

        title=pull_request.get("title"),
        content=pull_request.get("body"),
        author=author,

        created_at=pull_request.get("created_at"),
        updated_at=pull_request.get("updated_at"),

        url=pull_request.get("html_url"),

        context={
            "repository": repository,
        },

        metadata={
            "state": pull_request.get("state"),
            "draft": pull_request.get("draft"),
            "merged_at": pull_request.get("merged_at"),
            "closed_at": pull_request.get("closed_at"),
            "labels": labels,
            "locked": pull_request.get("locked"),
            "comments_count": pull_request.get("comments"),
            "base_branch": base.get("ref"),
            "head_branch": head.get("ref"),
            "base_repository": base_repo.get("full_name"),
            "head_repository": head_repo.get("full_name"),
        },

        provenance=Provenance(
            collector="github_rest_api",
            raw_reference=(
                f"pull_requests/pull_requests.json#{pull_number}"
            ),
        ),
    )


def normalize_commit(
    commit: dict[str, Any],
    repository: str,
) -> Artifact:
    """
    Convert one raw GitHub Commit into a universal Artifact.
    """

    sha = commit["sha"]

    commit_data = commit.get("commit") or {}

    message = commit_data.get("message") or ""

    # Use the first line of the commit message as the title.
    first_line = message.split("\n", 1)[0].strip()
    title = first_line if first_line else None

    # Prefer the top-level GitHub user login.
    # Fall back to the git commit author name.
    author_user = commit.get("author") or {}
    author_login = author_user.get("login")

    if not author_login:
        commit_author = commit_data.get("author") or {}
        author_login = commit_author.get("name")

    # Timestamps from the git commit metadata.
    commit_author_data = commit_data.get("author") or {}
    commit_committer_data = (
        commit_data.get("committer") or {}
    )

    created_at = commit_author_data.get("date")
    updated_at = commit_committer_data.get("date")

    context = {
        "repository": repository,
    }

    return Artifact(
        source=Source.GITHUB,
        source_scope=repository,
        artifact_type=ArtifactType.COMMIT,
        external_id=sha,

        title=title,
        content=message if message else None,
        author=author_login,

        created_at=created_at,
        updated_at=updated_at,

        url=commit.get("html_url"),

        context=context,

        metadata={
            "sha": sha,
            "committer_login": (
                (commit.get("committer") or {})
                .get("login")
            ),
            "committer_name": (
                commit_committer_data.get("name")
            ),
            "committer_date": (
                commit_committer_data.get("date")
            ),
            "verified": (
                (commit_data.get("verification") or {})
                .get("verified")
            ),
        },

        provenance=Provenance(
            collector="github_rest_api",
            raw_reference=(
                f"pull_requests/commits.json#{sha}"
            ),
        ),
    )


def _extract_document_title(
    content: str | None,
    path: str,
) -> str | None:
    """
    Extract a title from a decision document.

    Tries in order:
    1. YAML front-matter 'title' field.
    2. First markdown heading (# or ##).
    3. Filename stem.
    """

    if content:
        stripped = content.strip()

        # Try YAML front-matter.
        if stripped.startswith("---"):
            parts = stripped.split("---", 2)

            if len(parts) >= 3:
                frontmatter = parts[1]

                for line in frontmatter.split("\n"):
                    line = line.strip()

                    if line.lower().startswith("title:"):
                        title_value = (
                            line[len("title:"):].strip()
                        )

                        # Remove surrounding quotes.
                        if (
                            len(title_value) >= 2
                            and title_value[0] in ("'", '"')
                            and title_value[-1] == title_value[0]
                        ):
                            title_value = title_value[1:-1]

                        if title_value:
                            return title_value

        # Try first markdown heading.
        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("#"):
                heading = line.lstrip("#").strip()

                if heading:
                    return heading

    # Fall back to filename.
    from pathlib import PurePosixPath

    return PurePosixPath(path).stem or None


def normalize_document(
    document: dict[str, Any],
    repository: str,
) -> Artifact:
    """
    Convert one raw decision document into a universal Artifact.

    Documents come from GitHub's Contents API via
    the document discovery pipeline.

    Documents have no created_at/updated_at timestamps
    and no author from the GitHub Contents API.
    """

    path = document["path"]

    content = document.get("content") or ""
    content = content.strip() if content else None

    title = _extract_document_title(
        content,
        path,
    )

    return Artifact(
        source=Source.GITHUB,
        source_scope=repository,
        artifact_type=ArtifactType.DOCUMENT,
        external_id=path,

        title=title,
        content=content,
        author=None,

        created_at=None,
        updated_at=None,

        url=document.get("html_url"),

        context={
            "repository": repository,
        },

        metadata={
            "document_type": document.get(
                "document_type"
            ),
            "path": path,
            "sha": document.get("sha"),
            "size": document.get("size"),
            "download_url": document.get(
                "download_url"
            ),
        },

        provenance=Provenance(
            collector="github_rest_api",
            raw_reference=(
                f"documents/documents.json#{path}"
            ),
        ),
    )