import base64

from app.sources.github.client import GitHubClient
from app.sources.github.document_discovery import discover_documents


class GitHubCollector:
    """
    Coordinates collection of GitHub engineering history.

    Responsibilities:
    - Collect repository metadata
    - Collect issues
    - Collect issue comments
    - Collect issue timelines
    - Collect pull requests
    - Collect PR discussion comments
    - Collect PR commits
    - Discover decision-related documents
    - Download decision-document contents

    This class does NOT:
    - Save files
    - Normalize data
    - Call an LLM
    - Extract engineering decisions
    """

    def __init__(self):
        self.client = GitHubClient()

    def collect_repository_sample(
        self,
        owner: str,
        repo: str,
        sample_size: int = 20,
    ) -> dict:
        """
        Collect a sample dataset from one GitHub repository.
        """

        print(f"\nCollecting repository: {owner}/{repo}")

        # --------------------------------------------------
        # REPOSITORY METADATA
        # --------------------------------------------------

        print("\nFetching repository metadata...")

        repository = self.client.get_repository(
            owner=owner,
            repo=repo,
        )

        print("Repository metadata collected.")

        # --------------------------------------------------
        # ISSUES
        # --------------------------------------------------

        print("\nFetching closed issues...")

        issues = self.client.get_issues(
            owner=owner,
            repo=repo,
            state="closed",
            per_page=sample_size,
        )

        print(f"Collected {len(issues)} issues.")

        issue_comments = {}
        issue_timelines = {}

        for index, issue in enumerate(
            issues,
            start=1,
        ):
            issue_number = issue["number"]

            print(
                f"Processing issue "
                f"{index}/{len(issues)} "
                f"#{issue_number}"
            )

            comments = self.client.get_issue_comments(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            timeline = self.client.get_issue_timeline(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            issue_comments[str(issue_number)] = comments

            issue_timelines[str(issue_number)] = timeline

        # --------------------------------------------------
        # PULL REQUESTS
        # --------------------------------------------------

        print("\nFetching closed pull requests...")

        pull_requests = self.client.get_pull_requests(
            owner=owner,
            repo=repo,
            state="closed",
            per_page=sample_size,
        )

        print(
            f"Collected {len(pull_requests)} "
            f"pull requests."
        )

        pr_comments = {}
        pr_commits = {}

        for index, pull_request in enumerate(
            pull_requests,
            start=1,
        ):
            pull_number = pull_request["number"]

            print(
                f"Processing PR "
                f"{index}/{len(pull_requests)} "
                f"#{pull_number}"
            )

            comments = (
                self.client.get_pull_request_comments(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                )
            )

            commits = (
                self.client.get_pull_request_commits(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                )
            )

            pr_comments[str(pull_number)] = comments

            pr_commits[str(pull_number)] = commits

        # --------------------------------------------------
        # DECISION DOCUMENTS
        # --------------------------------------------------

        print("\nFetching repository tree...")

        repository_tree = self.client.get_repository_tree(
            owner=owner,
            repo=repo,
        )

        tree_items = repository_tree.get(
            "tree",
            [],
        )

        print(
            f"Repository tree contains "
            f"{len(tree_items)} items."
        )

        if repository_tree.get("truncated"):
            print(
                "WARNING: Repository tree was truncated "
                "by GitHub."
            )

            print(
                "Document discovery may therefore "
                "be incomplete."
            )

        print(
            "\nDiscovering potential "
            "decision documents..."
        )

        discovered_documents = discover_documents(
            tree_items
        )

        print(
            f"Discovered "
            f"{len(discovered_documents)} "
            f"potential decision documents."
        )

        decision_documents = []

        for index, document in enumerate(
            discovered_documents,
            start=1,
        ):
            document_path = document["path"]

            print(
                f"Downloading document "
                f"{index}/{len(discovered_documents)}: "
                f"{document_path}"
            )

            file_data = self.client.get_file_content(
                owner=owner,
                repo=repo,
                path=document_path,
            )

            encoded_content = file_data.get(
                "content",
                "",
            )

            encoding = file_data.get("encoding")

            # GitHub's Contents API normally returns
            # file contents using Base64 encoding.
            if encoding == "base64" and encoded_content:

                try:
                    content = base64.b64decode(
                        encoded_content
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )

                except Exception as error:

                    print(
                        f"WARNING: Failed to decode "
                        f"{document_path}: {error}"
                    )

                    content = ""

            else:
                print(
                    f"WARNING: No Base64 content returned "
                    f"for {document_path}."
                )

                content = ""

            decision_documents.append(
                {
                    **document,
                    "html_url": file_data.get(
                        "html_url"
                    ),
                    "download_url": file_data.get(
                        "download_url"
                    ),
                    "encoding": encoding,
                    "content": content,
                }
            )

        # --------------------------------------------------
        # DATASET SUMMARY
        # --------------------------------------------------

        total_issue_comments = sum(
            len(comments)
            for comments in issue_comments.values()
        )

        total_timeline_events = sum(
            len(events)
            for events in issue_timelines.values()
        )

        total_pr_comments = sum(
            len(comments)
            for comments in pr_comments.values()
        )

        total_pr_commits = sum(
            len(commits)
            for commits in pr_commits.values()
        )

        print("\nCOLLECTION COMPLETE")
        print("-" * 50)

        print(f"Repository: {owner}/{repo}")
        print(f"Issues: {len(issues)}")
        print(f"Issue comments: {total_issue_comments}")
        print(f"Timeline events: {total_timeline_events}")
        print(f"Pull requests: {len(pull_requests)}")
        print(f"PR discussion comments: {total_pr_comments}")
        print(f"PR commits: {total_pr_commits}")

        print(
            f"Decision documents: "
            f"{len(decision_documents)}"
        )

        # --------------------------------------------------
        # RETURN RAW DATASET
        # --------------------------------------------------

        return {
            "repository": repository,
            "issues": issues,
            "issue_comments": issue_comments,
            "issue_timelines": issue_timelines,
            "pull_requests": pull_requests,
            "pr_comments": pr_comments,
            "pr_commits": pr_commits,
            "decision_documents": decision_documents,
        }