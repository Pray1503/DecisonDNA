from typing import Optional
from pydantic import BaseModel, Field

class DecisionReconstruction(BaseModel):
    """
    Structured output format for the LLM decision reconstruction.
    """
    question: str = Field(description="The original user question.")
    
    insufficient_evidence: bool = Field(
        description="Set to true if the supplied evidence is insufficient to confidently answer the question."
    )
    
    answer: str = Field(description="The primary factual answer to the question based on evidence.")
    
    decision: Optional[str] = Field(
        default=None,
        description="The core decision that was made, if applicable."
    )
    
    reasoning_summary: str = Field(description="Summary of the reasoning behind the decision.")
    
    alternatives: Optional[list[str]] = Field(
        default=None,
        description="Alternatives that were considered, ONLY if explicitly supported by evidence."
    )
    
    implementation_evidence: Optional[str] = Field(
        default=None,
        description="How the decision was implemented (e.g., specific commits or PRs)."
    )
    
    outcome: Optional[str] = Field(
        default=None,
        description="The outcome or consequences of the decision, ONLY if supported by evidence."
    )
    
    evidence_artifact_ids: list[str] = Field(
        default_factory=list,
        description="List of artifact IDs that explicitly support the factual claims in this response. MUST NOT include any ID not provided in the evidence package."
    )
    
    evidence_chain: str = Field(description="A brief narrative explaining how the different pieces of evidence link together.")
    
    confidence: str = Field(description="Confidence level: HIGH, MEDIUM, or LOW.")
    
    uncertainty: Optional[str] = Field(
        default=None,
        description="Any uncertainties or missing context."
    )
