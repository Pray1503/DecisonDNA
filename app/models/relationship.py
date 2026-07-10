import hashlib
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class Relationship(BaseModel):
    """
    Universal representation of a directed relationship between two engineering artifacts.
    Provides deterministic and semantic links, e.g., Issue -> PR, PR -> Commit.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    relationship_id: str = Field(
        ...,
        description="Unique identifier for the relationship (typically a deterministic SHA-256 hash).",
    )
    source_id: str = Field(
        ...,
        description="The artifact_id of the source node.",
    )
    target_id: str = Field(
        ...,
        description="The artifact_id of the target node.",
    )
    relationship_type: str = Field(
        ...,
        description="Type of directed relationship (e.g., 'resolved_by', 'contains', 'references', 'depends_on', 'implements').",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score between 0.0 and 1.0 (default 1.0 for deterministic extraction).",
    )
    reasoning: str = Field(
        ...,
        description="Reasoning or description of why this link exists.",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supporting structured details (e.g., matched regex, line number).",
    )
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata tracing how the relationship was parsed and extracted.",
    )

    @classmethod
    def generate_id(
        cls,
        source_id: str,
        target_id: str,
        relationship_type: str,
    ) -> str:
        """
        Deterministic ID generation using SHA-256 hash of source, type, and target IDs.
        """
        key = f"{source_id.strip()}:{relationship_type.strip().lower()}:{target_id.strip()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize relationship to a plain dictionary.
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """
        Deserialize relationship from a dictionary.
        """
        return cls.model_validate(data)
