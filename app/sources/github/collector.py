from app.sources.github.client import GitHubClient


class GitHubCollector:
    """
    Collects GitHub engineering history using GitHubClient.

    The collector decides WHAT data DecisionDNA wants.
    It does not save files or perform AI processing.
    """

    def __init__(self):
        self.client = GitHubClient()

    def collect_repository_sample(
        self,
        owner: str,
        repo: str,
        sample_size: int = 20,
    ) -> dict:

        print(f"\nCollecting repository: {owner}/{repo}")

        repository = self.client.get_repository(
            owner=owner,
            repo=repo,
        )

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

        for index, issue in enumerate(issues, start=1):

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
            f"Collected {len(pull_requests)} pull requests."
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

            comments = self.client.get_pull_request_comments(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
            )

            commits = self.client.get_pull_request_commits(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
            )

            pr_comments[str(pull_number)] = comments
            pr_commits[str(pull_number)] = commits

        return {
            "repository": repository,
            "issues": issues,
            "issue_comments": issue_comments,
            "issue_timelines": issue_timelines,
            "pull_requests": pull_requests,
            "pr_comments": pr_comments,
            "pr_commits": pr_commits,
        }