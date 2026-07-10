import re
from typing import Optional
from collections import defaultdict

from app.evidence.graph import EvidenceGraph
from app.models.artifacts import Artifact
from app.models.relationships import Relationship

class RetrievalResult:
    def __init__(self):
        self.selected_artifacts: dict[str, Artifact] = {}
        self.selected_relationships: dict[str, Relationship] = {}
        self.retrieval_reasons: dict[str, str] = {}
        self.scores: dict[str, float] = {}

def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    stop_words = {"the", "and", "for", "with", "that", "this", "are", "from", "can", "not", "use", "has", "but", "have", "why", "what", "how", "did", "does"}
    return set(words) - stop_words

def score_artifact(query_tokens: set[str], artifact: Artifact) -> float:
    score = 0.0
    
    # Title match (high weight)
    if artifact.title:
        title_tokens = tokenize(artifact.title)
        title_overlap = len(query_tokens.intersection(title_tokens))
        score += title_overlap * 3.0
        
    # Content match (medium weight)
    if artifact.content:
        content_tokens = tokenize(artifact.content)
        content_overlap = len(query_tokens.intersection(content_tokens))
        # Add a slight normalization so long documents don't dominate purely by length
        # but still reward absolute matches
        score += content_overlap * 1.0 + (content_overlap / max(len(content_tokens), 1))
        
    # Boost decision documents slightly to prioritize them as they are core evidence
    if artifact.artifact_type.value == "document":
        score *= 1.2
        
    return score

def retrieve_evidence(
    query: str, 
    graph: EvidenceGraph, 
    top_k: int = 5,
    max_total_chars: int = 15000
) -> RetrievalResult:
    """
    Lightweight deterministic retrieval.
    Scores all artifacts, takes top-k, then expands 1 hop in the graph.
    Selects artifacts up to a size limit.
    """
    query_tokens = tokenize(query)
    
    # 1. Score all artifacts
    scored_artifacts = []
    for art in graph.artifacts.values():
        score = score_artifact(query_tokens, art)
        if score > 0:
            scored_artifacts.append((score, art))
            
    # Sort descending by score
    scored_artifacts.sort(key=lambda x: x[0], reverse=True)
    
    # Take top-k
    top_candidates = scored_artifacts[:top_k]
    
    result = RetrievalResult()
    current_chars = 0
    
    candidate_ids = [art.artifact_id for score, art in top_candidates]
    
    # 2. Add top candidates directly
    for score, art in top_candidates:
        art_chars = len(art.content or "") + len(art.title or "")
        
        # Always add the first candidate even if it exceeds limit slightly, 
        # otherwise stop if we hit the limit
        if current_chars + art_chars > max_total_chars and current_chars > 0:
            continue
            
        result.selected_artifacts[art.artifact_id] = art
        result.retrieval_reasons[art.artifact_id] = f"Direct match (score: {score:.2f})"
        result.scores[art.artifact_id] = score
        current_chars += art_chars
        
    # 3. Expand by 1 hop
    expanded_ids, traversed_rels = graph.expand_one_hop(list(result.selected_artifacts.keys()))
    
    for rel in traversed_rels:
        result.selected_relationships[rel.relationship_id] = rel
        
    # Try to add expanded artifacts, prioritizing those connected to top candidates
    for art_id in expanded_ids:
        if art_id in result.selected_artifacts:
            continue # already added
            
        art = graph.get_artifact(art_id)
        if not art:
            continue
            
        art_chars = len(art.content or "") + len(art.title or "")
        if current_chars + art_chars > max_total_chars:
            continue
            
        result.selected_artifacts[art.artifact_id] = art
        result.retrieval_reasons[art.artifact_id] = f"Graph expansion (1 hop)"
        current_chars += art_chars
        
    return result

def format_evidence_package(result: RetrievalResult) -> dict:
    """
    Format selected evidence into a compact dictionary.
    """
    package = {
        "artifacts": [],
        "relationships": []
    }
    
    for art in result.selected_artifacts.values():
        art_dict = {
            "artifact_id": art.artifact_id,
            "artifact_type": art.artifact_type.value,
            "title": art.title,
            "content": art.content,
            "author": art.author,
            "created_at": art.created_at.isoformat() if art.created_at else None,
            "updated_at": art.updated_at.isoformat() if art.updated_at else None,
            "url": art.url,
            "retrieval_reason": result.retrieval_reasons.get(art.artifact_id, "Unknown")
        }
        package["artifacts"].append(art_dict)
        
    for rel in result.selected_relationships.values():
        rel_dict = {
            "source_artifact_id": rel.source_artifact_id,
            "target_artifact_id": rel.target_artifact_id,
            "relationship_type": rel.relationship_type,
            "method": rel.method,
            "evidence": rel.evidence
        }
        package["relationships"].append(rel_dict)
        
    return package
