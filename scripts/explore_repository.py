import argparse
import json
from pathlib import Path

from app.sources.github.collector import GitHubCollector


RAW_DATA_DIRECTORY = Path("data/raw/github")


def save_json(
    path: Path,
    data,
) -> None:
    """
    Save Python data as formatted JSON.

    Parent directories are created automatically.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main():
    # --------------------------------------------------
    # COMMAND-LINE ARGUMENTS
    # --------------------------------------------------

    parser = argparse.ArgumentParser(
        description=(
            "Collect a sample of engineering history "
            "from a GitHub repository."
        )
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in owner/repo format",
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help=(
            "Number of issues and pull requests "
            "to request from GitHub."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # VALIDATE REPOSITORY NAME
    # --------------------------------------------------

    repository_parts = (
        args.repository
        .strip("/")
        .split("/")
    )

    if len(repository_parts) != 2:
        raise ValueError(
            "Repository must use owner/repo format. "
            "Example: backstage/backstage"
        )

    owner, repo = repository_parts

    # --------------------------------------------------
    # COLLECT DATA
    # --------------------------------------------------

    collector = GitHubCollector()

    dataset = collector.collect_repository_sample(
        owner=owner,
        repo=repo,
        sample_size=args.sample_size,
    )

    # --------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------

    output_directory = (
        RAW_DATA_DIRECTORY
        / owner
        / repo
    )

    # --------------------------------------------------
    # RAW FILES TO SAVE
    # --------------------------------------------------

    files_to_save = {
        "repository/metadata.json":
            dataset["repository"],

        "issues/issues.json":
            dataset["issues"],

        "issues/comments.json":
            dataset["issue_comments"],

        "issues/timelines.json":
            dataset["issue_timelines"],

        "pull_requests/pull_requests.json":
            dataset["pull_requests"],

        "pull_requests/comments.json":
            dataset["pr_comments"],

        "pull_requests/commits.json":
            dataset["pr_commits"],

        "documents/documents.json":
            dataset["decision_documents"],
    }

    # --------------------------------------------------
    # SAVE RAW DATA
    # --------------------------------------------------

    print("\nSaving raw GitHub data...")

    for relative_path, data in files_to_save.items():

        full_path = (
            output_directory
            / relative_path
        )

        save_json(
            path=full_path,
            data=data,
        )

        print(f"Saved {relative_path}")

    # --------------------------------------------------
    # CALCULATE DATASET STATISTICS
    # --------------------------------------------------

    total_issue_comments = sum(
        len(comments)
        for comments
        in dataset["issue_comments"].values()
    )

    total_timeline_events = sum(
        len(events)
        for events
        in dataset["issue_timelines"].values()
    )

    total_pr_comments = sum(
        len(comments)
        for comments
        in dataset["pr_comments"].values()
    )

    total_pr_commits = sum(
        len(commits)
        for commits
        in dataset["pr_commits"].values()
    )

    # --------------------------------------------------
    # DATASET SUMMARY
    # --------------------------------------------------

    print("\nDATASET SUMMARY")
    print("-" * 50)

    print(
        f"Repository: "
        f"{dataset['repository']['full_name']}"
    )

    print(
        f"Issues collected: "
        f"{len(dataset['issues'])}"
    )

    print(
        f"Pull requests collected: "
        f"{len(dataset['pull_requests'])}"
    )

    print(
        f"Issue comments: "
        f"{total_issue_comments}"
    )

    print(
        f"Timeline events: "
        f"{total_timeline_events}"
    )

    print(
        f"PR discussion comments: "
        f"{total_pr_comments}"
    )

    print(
        f"PR commits: "
        f"{total_pr_commits}"
    )

    print(
        f"Decision documents: "
        f"{len(dataset['decision_documents'])}"
    )

    print(
        f"\nRaw data saved to: "
        f"{output_directory}"
    )


if __name__ == "__main__":
    main()