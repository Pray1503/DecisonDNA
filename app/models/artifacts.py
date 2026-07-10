from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Source(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    SLACK = "slack"
    KUBERNETES = "kubernetes"
    LINEAR = "linear"
    DATADOG = "datadog"
    DOCUMENT = "document"
    OTHER = "other"


class ArtifactType(str, Enum):
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    DOCUMENT = "document"
    MESSAGE = "message"
    EVENT = "event"
    INCIDENT = "incident"
    OTHER = "other"


class Provenance(BaseModel):
    collector: str
    collected_at: datetime | None = None
    raw_reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    artifact_id: str | None = None

    source: Source
    source_scope: str
    artifact_type: ArtifactType
    external_id: str

    title: str | None = None
    content: str | None = None
    author: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    url: str | None = None

    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    provenance: Provenance

    @model_validator(mode="after")
    def generate_artifact_id(self) -> "Artifact":
        if self.artifact_id is None:
            self.artifact_id = (
                f"{self.source.value}:"
                f"{self.source_scope}:"
                f"{self.artifact_type.value}:"
                f"{self.external_id}"
            )

        return self