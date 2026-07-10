from typing import Dict, Any
from app.models.artifact import Artifact


class SlackNormalizer:
    """
    Normalizes Slack channel messages and retro inputs into Universal Artifacts.
    """
    def __init__(self, default_context: dict | None = None):
        self.default_context = default_context or {}

    def normalize_message(self, raw_msg: Dict[str, Any]) -> Artifact:
        msg_id = str(raw_msg.get("feedback_id") or "")
        if not msg_id:
            raise ValueError("Slack message must have a feedback_id")

        sprint = raw_msg.get("sprint", "unknown-sprint")
        project = raw_msg.get("project_id") or raw_msg.get("project")
        author = raw_msg.get("employee_id") or "unknown"
        
        # Combine opinion and suggestions as content
        opinion = raw_msg.get("opinion") or ""
        suggestion = raw_msg.get("suggestion") or ""
        content = f"Opinion: {opinion}\nSuggestion: {suggestion}"
        
        title = f"Slack Post in {sprint} by {author}"

        context = {**self.default_context}
        if project:
            context["project"] = project

        metadata = {
            "sprint": sprint,
            "difficulty_rating": raw_msg.get("difficulty_rating"),
            "referenced_adr": raw_msg.get("adr_id"),
        }

        artifact_id = Artifact.generate_id(
            source="slack",
            source_type="chat",
            external_id=msg_id,
            context=context,
        )

        provenance = {
            "connector": "SlackConnector",
            "version": "1.0.0",
        }

        return Artifact(
            artifact_id=artifact_id,
            source="slack",
            source_type="chat",
            external_id=msg_id,
            title=title,
            content=content,
            author=author,
            timestamps={"created_at": sprint},
            context=context,
            metadata=metadata,
            provenance=provenance,
        )
