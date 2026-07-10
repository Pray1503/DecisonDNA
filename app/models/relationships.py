import hashlib
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class Relationship(BaseModel):
    """
    Universal Relationship representing a directed connection
    between two Artifacts (or an Artifact and an unresolved target).
    """

    relationship_id: str = Field(
        default="",
        description="Deterministic ID: hash(source_id + target_id + relationship_type)",
    )

    source_artifact_id: str
    target_artifact_id: str
    
    relationship_type: str = Field(
        description="The semantic type of the relationship, e.g., 'references', 'contains_commit'."
    )
    
    method: Literal["deterministic", "semantic"] = Field(
        default="deterministic",
    )
    
    evidence: str | None = Field(
        default=None,
        description="Text or context justifying the relationship.",
    )
    
    confidence: float = Field(
        default=1.0,
        description="Confidence score for the relationship (0.0 to 1.0).",
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def generate_relationship_id(self) -> "Relationship":
        """
        Deterministically generate the relationship_id based on core fields.
        """
        if not self.relationship_id:
            core_string = f"{self.source_artifact_id}::{self.relationship_type}::{self.target_artifact_id}"
            
            # Use SHA-256 for deterministic hashing
            hash_hex = hashlib.sha256(core_string.encode("utf-8")).hexdigest()
            
            # Create a readable prefix + short hash
            self.relationship_id = f"rel:{self.relationship_type}:{hash_hex[:16]}"

        return self
