from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class Artifact(BaseModel):
    """
    Universal representation of any engineering evidence in DecisionDNA.
    Converts and unifies GitHub issues, PRs, commits, Slack messages,
    Jira tickets, etc., into a consistent model.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    artifact_id: str = Field(
        ...,
        description="Unique identifier for the artifact within DecisionDNA.",
    )
    source: str = Field(
        ...,
        description="Identifier of the source system (e.g., 'github', 'jira').",
    )
    source_type: str = Field(
        ...,
        description="Type of the artifact in the source system (e.g., 'issue', 'pull_request', 'commit', 'adr').",
    )
    external_id: str = Field(
        ...,
        description="Unique identifier of the artifact in the external system.",
    )
    title: str = Field(
        ...,
        description="Title or short summary of the artifact.",
    )
    content: str = Field(
        ...,
        description="Main text body or description of the artifact.",
    )
    author: str = Field(
        ...,
        description="Author identifier or username.",
    )
    timestamps: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of relevant timestamps (e.g., created_at, updated_at).",
    )
    url: Optional[str] = Field(
        None,
        validation_alias="URL",
        serialization_alias="url",
        description="Direct URL pointing to the external artifact.",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual/relational details (e.g., repository name, project key, branch).",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata specific to the source type (e.g., status, tags, labels).",
    )
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tracing how the artifact was imported and processed.",
    )

    @classmethod
    def generate_id(
        cls,
        source: str,
        source_type: str,
        external_id: str,
        context: Dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a unique, consistent artifact identifier.
        """
        src = source.strip().lower()
        stype = source_type.strip().lower()
        ext_id = str(external_id).strip()

        parts = [src]

        # Use repo if available for context namespacing
        if context:
            repo = context.get("repository") or context.get("repo")
            if repo:
                parts.append(str(repo).strip().lower())
            elif "project" in context:
                project = context.get("project")
                if project:
                    parts.append(str(project).strip().lower())

        parts.extend([stype, ext_id])
        return ":".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize artifact to a plain dictionary.
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        """
        Deserialize artifact from a dictionary.
        """
        return cls.model_validate(data)
