import argparse
import json
from pathlib import Path

from app.sources.github.collector import GitHubCollector


RAW_DATA_DIRECTORY = Path("data/raw/github")


def save_json(
    path: Path,
    data,
) -> None:

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

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "repository",
        help="GitHub repository in owner/repo format",
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    parts = args.repository.strip("/").split("/")

    if len(parts) != 2:
        raise ValueError(
            "Repository must use owner/repo format."
        )

    owner, repo = parts

    collector = GitHubCollector()

    dataset = collector.collect_repository_sample(
        owner=owner,
        repo=repo,
        sample_size=args.sample_size,
    )

    output_directory = (
        RAW_DATA_DIRECTORY
        / owner
        / repo
    )

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

    }

    print("\nSaving raw GitHub data...")

    for filename, data in files_to_save.items():

        save_json(
            output_directory / filename,
            data,
        )

        print(f"Saved {filename}")

    print("\nDATASET SUMMARY")
    print("-" * 50)

    print(f"Repository: {owner}/{repo}")

    print(
        f"Issues collected: "
        f"{len(dataset['issues'])}"
    )

    print(
        f"Pull requests collected: "
        f"{len(dataset['pull_requests'])}"
    )

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

    print(f"Issue comments: {total_issue_comments}")
    print(f"Timeline events: {total_timeline_events}")
    print(f"PR discussion comments: {total_pr_comments}")
    print(f"PR commits: {total_pr_commits}")

    print(
        f"\nRaw data saved to: "
        f"{output_directory}"
    )


if __name__ == "__main__":
    main()