import json

from app.models.artifacts import (
    Artifact,
    ArtifactType,
    Provenance,
    Source,
)


def print_artifact(label: str, artifact: Artifact) -> None:
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
    issue_artifact = Artifact(
        source=Source.GITHUB,
        source_scope="backstage/backstage",
        artifact_type=ArtifactType.ISSUE,
        external_id="34814",
        title="Example GitHub Issue",
        content="Database queries become slower as the events table grows.",
        author="example-user",
        url="https://github.com/backstage/backstage/issues/34814",
        context={
            "repository": "backstage/backstage",
        },
        metadata={
            "state": "closed",
            "labels": ["performance", "database"],
        },
        provenance=Provenance(
            collector="github_rest_api",
            raw_reference="issues/issues.json#34814",
        ),
    )

    pr_artifact = Artifact(
        source=Source.GITHUB,
        source_scope="backstage/backstage",
        artifact_type=ArtifactType.PULL_REQUEST,
        external_id="34815",
        title="Introduce weekly table partitioning",
        content="This PR introduces weekly partitioning for the events table.",
        author="example-developer",
        url="https://github.com/backstage/backstage/pull/34815",
        context={
            "repository": "backstage/backstage",
        },
        metadata={
            "state": "closed",
            "merged": True,
            "base_branch": "master",
            "head_branch": "weekly-partitioning",
        },
        provenance=Provenance(
            collector="github_rest_api",
            raw_reference="pull_requests/pull_requests.json#34815",
        ),
    )

    commit_artifact = Artifact(
        source=Source.GITHUB,
        source_scope="backstage/backstage",
        artifact_type=ArtifactType.COMMIT,
        external_id="abc123def456",
        title="Add weekly partitioning support",
        content="Add weekly partitioning support for the events table.",
        author="example-developer",
        url="https://github.com/backstage/backstage/commit/abc123def456",
        context={
            "repository": "backstage/backstage",
        },
        metadata={
            "sha": "abc123def456",
        },
        provenance=Provenance(
            collector="github_rest_api",
            raw_reference="pull_requests/commits.json#abc123def456",
        ),
    )

    adr_artifact = Artifact(
        source=Source.GITHUB,
        source_scope="backstage/backstage",
        artifact_type=ArtifactType.DOCUMENT,
        external_id=(
            "docs/architecture-decisions/"
            "adr010-luxon-date-library.md"
        ),
        title="Use Luxon as the default date library",
        content="The project adopts Luxon as the default library for date handling.",
        author=None,
        url=(
            "https://github.com/backstage/backstage/blob/master/"
            "docs/architecture-decisions/adr010-luxon-date-library.md"
        ),
        context={
            "repository": "backstage/backstage",
        },
        metadata={
            "document_type": "adr",
            "path": (
                "docs/architecture-decisions/"
                "adr010-luxon-date-library.md"
            ),
        },
        provenance=Provenance(
            collector="github_rest_api",
            raw_reference="documents/documents.json#adr010-luxon-date-library.md",
        ),
    )

    artifacts = [
        ("ISSUE ARTIFACT", issue_artifact),
        ("PULL REQUEST ARTIFACT", pr_artifact),
        ("COMMIT ARTIFACT", commit_artifact),
        ("ADR ARTIFACT", adr_artifact),
    ]

    for label, artifact in artifacts:
        print_artifact(label, artifact)


if __name__ == "__main__":
    main()