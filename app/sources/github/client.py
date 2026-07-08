import requests

from app.core.config import GITHUB_TOKEN


class GitHubClient:
    """
    Low-level client for communicating with the GitHub REST API.

    Responsibilities:
    - Authentication
    - HTTP requests
    - GitHub endpoints
    - Returning raw API responses

    This class does NOT:
    - Save files
    - Call an LLM
    - Extract decisions
    - Correlate artifacts
    """

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        accept: str | None = None,
    ):
        """
        Internal reusable GET method.
        """

        url = f"{self.BASE_URL}{endpoint}"

        headers = {}

        if accept:
            headers["Accept"] = accept

        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict:
        """
        Fetch repository metadata.
        """

        return self._get(
            f"/repos/{owner}/{repo}"
        )

    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        per_page: int = 20,
    ) -> list[dict]:
        """
        Fetch issues.

        IMPORTANT:
        GitHub's Issues endpoint also returns pull requests.

        Items containing the "pull_request" field are removed.
        """

        data = self._get(
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": state,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc",
            },
        )

        return [
            item
            for item in data
            if "pull_request" not in item
        ]

    def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        per_page: int = 20,
    ) -> list[dict]:
        """
        Fetch pull requests.
        """

        return self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc",
            },
        )

    def get_issue_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Fetch discussion comments for one issue.
        """

        return self._get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            params={
                "per_page": per_page,
            },
        )

    def get_issue_timeline(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Fetch timeline events for one issue.

        Timeline events can contain useful relationships such as:

        - cross references
        - commits
        - closures
        - references
        - linked pull requests
        """

        return self._get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/timeline",
            params={
                "per_page": per_page,
            },
            accept="application/vnd.github+json",
        )

    def get_pull_request_comments(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Fetch general PR discussion comments.

        IMPORTANT:

        PR discussion comments use the Issues Comments endpoint
        because GitHub treats pull requests as issues internally.

        This does NOT fetch inline code review comments.
        """

        return self._get(
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
            params={
                "per_page": per_page,
            },
        )

    def get_pull_request_commits(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Fetch commits belonging to one pull request.
        """

        return self._get(
            f"/repos/{owner}/{repo}/pulls/{pull_number}/commits",
            params={
                "per_page": per_page,
            },
        )