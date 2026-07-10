import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.models.artifact import Artifact


class GitHubNormalizer:
    """
    Normalizes raw GitHub JSON data (from REST API or synthetic datasets)
    into the Universal Artifact Schema.
    """

    VERSION = "1.0.0"

    def __init__(self, default_context: Optional[Dict[str, Any]] = None):
        self.default_context = default_context or {}

    def _get_provenance(self, raw_path: Optional[str] = None) -> Dict[str, Any]:
        return {
            "imported_at": datetime.utcnow().isoformat(),
            "normalizer": "GitHubNormalizer",
            "version": self.VERSION,
            "raw_file_path": raw_path,
        }

    def _extract_repository(
        self, raw_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Helper to find repository name from context or raw object.
        """
        if "repository" in context:
            return context["repository"]
        if "repo" in context:
            return context["repo"]
        if "repository" in raw_data:
            return raw_data["repository"]

        # Parse from repository_url: e.g. "https://api.github.com/repos/owner/repo"
        repo_url = raw_data.get("repository_url")
        if repo_url and "/repos/" in repo_url:
            parts = repo_url.split("/repos/")
            if len(parts) > 1:
                return parts[1]

        # Parse from html_url: e.g. "https://github.com/owner/repo/pull/1"
        html_url = raw_data.get("html_url")
        if html_url and "github.com/" in html_url:
            parts = html_url.split("github.com/")[1].split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"

        # Check PR base repo
        base = raw_data.get("base")
        if isinstance(base, dict) and "repo" in base:
            repo_info = base["repo"]
            if isinstance(repo_info, dict) and "full_name" in repo_info:
                return repo_info["full_name"]

        return None

    def normalize_issue(
        self,
        raw_issue: Dict[str, Any],
        comments: Optional[List[Dict[str, Any]]] = None,
        timeline: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        raw_path: Optional[str] = None,
    ) -> Artifact:
        """
        Normalize a raw GitHub issue (with optional comments and timeline events).
        """
        ctx = {**self.default_context, **(context or {})}
        repo = self._extract_repository(raw_issue, ctx)
        if repo:
            ctx["repository"] = repo

        issue_number = str(raw_issue.get("number") or raw_issue.get("issue_number") or raw_issue.get("external_id") or "")
        if not issue_number:
            raise ValueError("Issue must have a number / external_id")

        # Extract basic fields
        title = raw_issue.get("title") or f"Issue #{issue_number}"
        
        # Determine author
        author = "unknown"
        user_info = raw_issue.get("user")
        if isinstance(user_info, dict) and "login" in user_info:
            author = user_info["login"]
        elif raw_issue.get("author"):
            author = raw_issue["author"]

        # Timestamps
        timestamps = {}
        for ts_key in ["created_at", "updated_at", "closed_at"]:
            if raw_issue.get(ts_key):
                timestamps[ts_key] = raw_issue[ts_key]

        # URL
        url = raw_issue.get("html_url")

        # Compile body content and format discussion
        body = raw_issue.get("body") or ""
        content_parts = [body]

        processed_comments = []
        if comments:
            content_parts.append("\n\n--- Discussion ---")
            for c in comments:
                c_author = "unknown"
                c_user = c.get("user")
                if isinstance(c_user, dict) and "login" in c_user:
                    c_author = c_user["login"]
                elif c.get("author"):
                    c_author = c["author"]

                c_created = c.get("created_at") or c.get("date") or ""
                c_body = c.get("body") or ""
                
                content_parts.append(
                    f"\n* **@{c_author}** ({c_created}):\n{c_body}"
                )
                processed_comments.append({
                    "author": c_author,
                    "created_at": c_created,
                    "body": c_body
                })

        content = "\n".join(content_parts)

        # Build metadata
        labels = []
        for l in raw_issue.get("labels", []):
            if isinstance(l, dict) and "name" in l:
                labels.append(l["name"])
            elif isinstance(l, str):
                labels.append(l)

        metadata = {
            "state": raw_issue.get("state") or raw_issue.get("status") or "open",
            "labels": labels,
            "comments_count": len(comments) if comments else raw_issue.get("comments", 0),
            "timeline_events_count": len(timeline) if timeline else 0,
            "comments": processed_comments,
        }

        if timeline:
            metadata["timeline"] = timeline

        # Extract linked PRs or commits from timeline or body
        linked_prs = []
        linked_commits = []
        
        # Simple regex helper to find references
        body_text = f"{body} " + " ".join([c.get("body", "") for c in comments or []])
        # Find #123 (PRs or Issues)
        refs = re.findall(r'#(\d+)', body_text)
        if refs:
            metadata["referenced_ids"] = list(set(refs))

        artifact_id = Artifact.generate_id(
            source="github",
            source_type="issue",
            external_id=issue_number,
            context=ctx,
        )

        return Artifact(
            artifact_id=artifact_id,
            source="github",
            source_type="issue",
            external_id=issue_number,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            url=url,
            context=ctx,
            metadata=metadata,
            provenance=self._get_provenance(raw_path),
        )

    def normalize_pull_request(
        self,
        raw_pr: Dict[str, Any],
        comments: Optional[List[Dict[str, Any]]] = None,
        commits: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        raw_path: Optional[str] = None,
    ) -> Artifact:
        """
        Normalize a raw GitHub Pull Request (with optional discussion comments and commits).
        """
        ctx = {**self.default_context, **(context or {})}
        repo = self._extract_repository(raw_pr, ctx)
        if repo:
            ctx["repository"] = repo

        pr_number = str(raw_pr.get("number") or raw_pr.get("pr_number") or raw_pr.get("external_id") or "")
        if not pr_number:
            # Fallback to pr_id if no number
            pr_number = str(raw_pr.get("pr_id") or "")
            if not pr_number:
                raise ValueError("Pull Request must have a number or pr_id")

        title = raw_pr.get("title") or f"Pull Request #{pr_number}"
        
        # Author
        author = "unknown"
        user_info = raw_pr.get("user")
        if isinstance(user_info, dict) and "login" in user_info:
            author = user_info["login"]
        elif raw_pr.get("author"):
            author = raw_pr["author"]

        # Timestamps
        timestamps = {}
        for ts_key in ["created_at", "updated_at", "closed_at", "merged_at"]:
            if raw_pr.get(ts_key):
                timestamps[ts_key] = raw_pr[ts_key]

        url = raw_pr.get("html_url")

        # Compile body description + Commits summary + Comments discussion
        body = raw_pr.get("body") or ""
        content_parts = [body]

        # Append Commits Summary
        processed_commits = []
        if commits:
            content_parts.append("\n\n--- Commits ---")
            for c in commits:
                c_sha = c.get("sha") or c.get("commit_sha") or ""
                c_message = c.get("commit", {}).get("message") if isinstance(c.get("commit"), dict) else c.get("message") or ""
                c_author = c.get("author", {}).get("login") if isinstance(c.get("author"), dict) else c.get("author") or ""
                
                content_parts.append(
                    f"\n* {c_sha[:8] if c_sha else ''} - {c_message} (by @{c_author})"
                )
                processed_commits.append({
                    "sha": c_sha,
                    "message": c_message,
                    "author": c_author
                })

        # Append Comments Discussion
        processed_comments = []
        if comments:
            content_parts.append("\n\n--- Discussion ---")
            for c in comments:
                c_author = "unknown"
                c_user = c.get("user")
                if isinstance(c_user, dict) and "login" in c_user:
                    c_author = c_user["login"]
                elif c.get("author"):
                    c_author = c["author"]

                c_created = c.get("created_at") or c.get("date") or ""
                c_body = c.get("body") or ""
                
                content_parts.append(
                    f"\n* **@{c_author}** ({c_created}):\n{c_body}"
                )
                processed_comments.append({
                    "author": c_author,
                    "created_at": c_created,
                    "body": c_body
                })

        content = "\n".join(content_parts)

        # Labels
        labels = []
        for l in raw_pr.get("labels", []):
            if isinstance(l, dict) and "name" in l:
                labels.append(l["name"])
            elif isinstance(l, str):
                labels.append(l)

        # Custom fields from synthetic data
        jira_ticket = raw_pr.get("jira_ticket") or raw_pr.get("jira_key")
        if not jira_ticket:
            # Try to extract AL5-1 style jira ticket from title or body
            matches = re.findall(r'([A-Z][A-Z0-9]+-\d+)', f"{title} {body}")
            for m in matches:
                if not m.startswith("ADR-"):
                    jira_ticket = m
                    break

        metadata = {
            "pr_id": raw_pr.get("pr_id"),
            "pr_number": raw_pr.get("pr_number") or raw_pr.get("number"),
            "state": raw_pr.get("state") or raw_pr.get("status") or "open",
            "merged": raw_pr.get("merged") or (raw_pr.get("status") == "Merged") or bool(raw_pr.get("merged_at")),
            "labels": labels,
            "comments_count": len(comments) if comments else 0,
            "commits_count": len(commits) if commits else 0,
            "commits": processed_commits,
            "comments": processed_comments,
            "jira_ticket": jira_ticket,
            "adr": raw_pr.get("adr"),
        }

        artifact_id = Artifact.generate_id(
            source="github",
            source_type="pull_request",
            external_id=pr_number,
            context=ctx,
        )

        return Artifact(
            artifact_id=artifact_id,
            source="github",
            source_type="pull_request",
            external_id=pr_number,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            url=url,
            context=ctx,
            metadata=metadata,
            provenance=self._get_provenance(raw_path),
        )

    def normalize_commit(
        self,
        raw_commit: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        raw_path: Optional[str] = None,
    ) -> Artifact:
        """
        Normalize a raw GitHub commit.
        """
        ctx = {**self.default_context, **(context or {})}
        repo = self._extract_repository(raw_commit, ctx)
        if repo:
            ctx["repository"] = repo

        sha = raw_commit.get("sha") or raw_commit.get("commit_sha") or ""
        if not sha:
            raise ValueError("Commit must have a sha / commit_sha")

        # Commit message
        full_message = ""
        commit_details = raw_commit.get("commit")
        if isinstance(commit_details, dict) and "message" in commit_details:
            full_message = commit_details["message"]
        elif raw_commit.get("message"):
            full_message = raw_commit["message"]

        # Parse first line as title, rest as content
        msg_lines = full_message.split("\n", 1)
        title = msg_lines[0] if msg_lines else f"Commit {sha[:8]}"
        content = full_message

        # Author
        author = "unknown"
        commit_details = raw_commit.get("commit")
        if isinstance(commit_details, dict):
            commit_author = commit_details.get("author")
            if isinstance(commit_author, dict) and "name" in commit_author:
                author = commit_author["name"]
        
        user_author = raw_commit.get("author")
        if isinstance(user_author, dict) and "login" in user_author:
            author = user_author["login"]
        elif isinstance(user_author, str) and user_author:
            author = user_author

        # Timestamps
        timestamps = {}
        commit_details = raw_commit.get("commit")
        if isinstance(commit_details, dict):
            committer_info = commit_details.get("committer") or commit_details.get("author")
            if isinstance(committer_info, dict) and "date" in committer_info:
                timestamps["committed_at"] = committer_info["date"]
                timestamps["created_at"] = committer_info["date"]
        
        if raw_commit.get("date"):
            timestamps["committed_at"] = raw_commit["date"]
            timestamps["created_at"] = raw_commit["date"]

        url = raw_commit.get("html_url")

        # Metadata
        parents = []
        raw_parents = raw_commit.get("parents", [])
        for p in raw_parents:
            if isinstance(p, dict) and "sha" in p:
                parents.append(p["sha"])
            elif isinstance(p, str):
                parents.append(p)

        # Parse AL5-1 style JIRA ticket or ADR-0001 from commit message
        jira_ticket = None
        matches_jira = re.findall(r'([A-Z][A-Z0-9]+-\d+)', full_message)
        for m in matches_jira:
            if not m.startswith("ADR-"):
                jira_ticket = m
                break

        adr_id = None
        match_adr = re.search(r'(ADR-\d+)', full_message)
        if match_adr:
            adr_id = match_adr.group(1)

        metadata = {
            "parents": parents,
            "pull_request": raw_commit.get("pull_request"),
            "jira_ticket": jira_ticket,
            "adr": adr_id or raw_commit.get("adr"),
        }

        artifact_id = Artifact.generate_id(
            source="github",
            source_type="commit",
            external_id=sha,
            context=ctx,
        )

        return Artifact(
            artifact_id=artifact_id,
            source="github",
            source_type="commit",
            external_id=sha,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            url=url,
            context=ctx,
            metadata=metadata,
            provenance=self._get_provenance(raw_path),
        )

    def normalize_adr(
        self,
        raw_adr: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        raw_path: Optional[str] = None,
    ) -> Artifact:
        """
        Normalize an Architecture Decision Record (ADR) file.
        Input can be structured (from OrgMemory JSON) or semi-structured markdown.
        """
        ctx = {**self.default_context, **(context or {})}
        
        # Link project if there's related_project (e.g. PRJ-006)
        if raw_adr.get("related_project"):
            ctx["project"] = raw_adr["related_project"]
        
        # Use filename or adr_id as external_id
        adr_id = raw_adr.get("adr_id") or raw_adr.get("id") or ""
        if not adr_id and raw_path:
            # Try to extract from path (e.g., "docs/adr/0001-some-decision.md" -> "0001")
            filename = raw_path.split("/")[-1].split(".")[0]
            adr_id = filename
        
        if not adr_id:
            raise ValueError("ADR must have an adr_id or identifiable filename")

        title = raw_adr.get("title") or f"ADR {adr_id}"
        author = raw_adr.get("owner") or raw_adr.get("author") or "unknown"
        
        timestamps = {}
        if raw_adr.get("date"):
            timestamps["created_at"] = raw_adr["date"]

        url = raw_adr.get("html_url") or raw_adr.get("url")

        # Construct beautiful markdown text if input is a structured dictionary
        # (this maps nicely to the generic content field for AI semantic analysis)
        content_body = raw_adr.get("content")
        if not content_body:
            # Compile structured fields into Markdown
            sections = []
            sections.append(f"# {adr_id}: {title}\n")
            sections.append(f"**Status**: {raw_adr.get('status', 'Accepted')}")
            if raw_adr.get("date"):
                sections.append(f"**Date**: {raw_adr.get('date')}")
            if author:
                sections.append(f"**Owner**: {author}")
            sections.append("")

            # Main ADR sections
            for field in [
                "context",
                "problem",
                "alternatives",
                "decision",
                "reason",
                "consequences",
                "expected_benefits",
                "potential_risks",
                "outcome",
            ]:
                if raw_adr.get(field):
                    header = field.replace("_", " ").title()
                    sections.append(f"## {header}\n{raw_adr[field]}\n")

            content_body = "\n".join(sections)

        metadata = {
            "status": raw_adr.get("status") or "Accepted",
            "tags": raw_adr.get("tags") or [],
            "complexity": raw_adr.get("complexity"),
            "priority": raw_adr.get("priority"),
            "linked_jira_tickets": raw_adr.get("linked_jira_tickets") or [],
            "linked_pull_requests": raw_adr.get("linked_pull_requests") or [],
            "linked_deployments": raw_adr.get("linked_deployments") or [],
            "linked_incidents": raw_adr.get("linked_incidents") or [],
            "outcome_summary": raw_adr.get("outcome"),
        }

        artifact_id = Artifact.generate_id(
            source="github",
            source_type="adr",
            external_id=adr_id,
            context=ctx,
        )

        return Artifact(
            artifact_id=artifact_id,
            source="github",
            source_type="adr",
            external_id=adr_id,
            title=title,
            content=content_body,
            author=author,
            timestamps=timestamps,
            url=url,
            context=ctx,
            metadata=metadata,
            provenance=self._get_provenance(raw_path),
        )
