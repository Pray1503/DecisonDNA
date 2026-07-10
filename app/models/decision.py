import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Decision(BaseModel):
    """
    Structured engineering decision reconstructed from a cluster of artifacts.
    Captures the decision lifecycle, rationale, constraints, outcomes,
    and supporting evidence.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    decision_id: str = Field(
        ...,
        description="Unique identifier for the decision.",
    )
    title: str = Field(
        ...,
        description="Short summary of the decision.",
    )
    problem: str = Field(
        ...,
        description="The core problem being addressed by the decision.",
    )
    context: str = Field(
        ...,
        description="Contextual background or trigger events for the decision.",
    )
    constraints: str = Field(
        ...,
        description="Architectural, business, or operational constraints identified.",
    )
    alternatives: str = Field(
        ...,
        description="Alternative options considered during the decision process.",
    )
    decision: str = Field(
        ...,
        description="The chosen technical direction or architecture solution.",
    )
    reasoning: str = Field(
        ...,
        description="The technical rationale or justification for the selection.",
    )
    implementation: str = Field(
        ...,
        description="Summary of how the decision was implemented (derived from PRs/commits).",
    )
    outcomes: str = Field(
        ...,
        description="Post-implementation outcomes, status, or mitigations (derived from incidents/deployments).",
    )
    lessons: str = Field(
        ...,
        description="Lessons learned, operational consequences, or follow-ups.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score of the decision reconstruction (0.0 to 1.0).",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of artifact_ids that served as evidence for this decision.",
    )

    @classmethod
    def generate_id(cls, adr_id: str) -> str:
        """
        Generates a unique ID from the seed ADR external ID (e.g. ADR-0001).
        """
        key = f"decision:{adr_id.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize decision to a plain dictionary.
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """
        Deserialize decision from a dictionary.
        """
        return cls.model_validate(data)
