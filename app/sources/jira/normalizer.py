from typing import Dict, Any
from app.models.artifact import Artifact


class JiraNormalizer:
    """
    Normalizes JIRA API ticket representations into Universal Artifacts.
    """
    def __init__(self, default_context: dict | None = None):
        self.default_context = default_context or {}

    def normalize_ticket(self, raw_ticket: Dict[str, Any]) -> Artifact:
        ticket_id = str(raw_ticket.get("ticket_id") or raw_ticket.get("key") or "")
        if not ticket_id:
            raise ValueError("JIRA ticket must have a ticket_id")

        title = raw_ticket.get("title") or f"Jira Ticket {ticket_id}"
        content = raw_ticket.get("description") or ""
        author = raw_ticket.get("owner") or raw_ticket.get("reporter") or "unknown"
        project = raw_ticket.get("project")

        timestamps = {}
        if raw_ticket.get("created_date") or raw_ticket.get("created_at"):
            timestamps["created_at"] = raw_ticket.get("created_date") or raw_ticket.get("created_at")
        if raw_ticket.get("resolved_date") or raw_ticket.get("resolved_at"):
            timestamps["resolved_at"] = raw_ticket.get("resolved_date") or raw_ticket.get("resolved_at")

        context = {**self.default_context}
        if project:
            context["project"] = project

        metadata = {
            "ticket_type": raw_ticket.get("type") or raw_ticket.get("issue_type"),
            "status": raw_ticket.get("status"),
            "sprint": raw_ticket.get("sprint"),
            "priority": raw_ticket.get("priority"),
            "dependencies": raw_ticket.get("dependencies") or [],
            "adr": raw_ticket.get("adr"),
        }

        artifact_id = Artifact.generate_id(
            source="jira",
            source_type="issue",
            external_id=ticket_id,
            context=context,
        )

        provenance = {
            "connector": "JiraConnector",
            "version": "1.0.0",
        }

        return Artifact(
            artifact_id=artifact_id,
            source="jira",
            source_type="issue",
            external_id=ticket_id,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            context=context,
            metadata=metadata,
            provenance=provenance,
        )
