from collections import defaultdict
from typing import Optional

from app.models.artifacts import Artifact
from app.models.relationships import Relationship

class EvidenceGraph:
    """
    Tiny in-memory evidence graph for traversing relationships between Artifacts.
    """
    def __init__(self):
        self.artifacts: dict[str, Artifact] = {}
        self.relationships: dict[str, Relationship] = {}
        
        # Adjacency lists storing (target_id, relationship)
        self.outgoing: dict[str, list[tuple[str, Relationship]]] = defaultdict(list)
        self.incoming: dict[str, list[tuple[str, Relationship]]] = defaultdict(list)
        
        self.resolved_edge_count = 0
        self.unresolved_edge_count = 0
        
    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts[artifact.artifact_id] = artifact
        
    def add_relationship(self, relationship: Relationship) -> None:
        self.relationships[relationship.relationship_id] = relationship
        
        src = relationship.source_artifact_id
        tgt = relationship.target_artifact_id
        
        self.outgoing[src].append((tgt, relationship))
        self.incoming[tgt].append((src, relationship))
        
        if tgt.startswith("unresolved:"):
            self.unresolved_edge_count += 1
        else:
            self.resolved_edge_count += 1
            
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self.artifacts.get(artifact_id)
        
    def get_outgoing(self, artifact_id: str) -> list[tuple[str, Relationship]]:
        return self.outgoing.get(artifact_id, [])
        
    def get_incoming(self, artifact_id: str) -> list[tuple[str, Relationship]]:
        return self.incoming.get(artifact_id, [])
        
    def get_all_neighbors(self, artifact_id: str) -> list[tuple[str, Relationship]]:
        return self.get_outgoing(artifact_id) + self.get_incoming(artifact_id)
        
    def expand_one_hop(self, artifact_ids: list[str]) -> tuple[set[str], list[Relationship]]:
        """
        Expand from a set of starting artifacts by one hop.
        Returns the set of expanded artifact IDs (including the starting ones),
        and the list of relationships traversed.
        """
        expanded_ids = set(artifact_ids)
        traversed_relationships = []
        
        for art_id in artifact_ids:
            for neighbor_id, rel in self.get_all_neighbors(art_id):
                # Don't add unresolved targets to our artifact set, since they aren't artifacts.
                if not neighbor_id.startswith("unresolved:"):
                    expanded_ids.add(neighbor_id)
                
                # Keep track of the relationship used to reach it
                if rel not in traversed_relationships:
                    traversed_relationships.append(rel)
                    
        return expanded_ids, traversed_relationships

    def validate(self) -> list[str]:
        """
        Validate graph invariants.
        Returns a list of error strings, empty if valid.
        """
        errors = []
        for rel in self.relationships.values():
            if rel.source_artifact_id not in self.artifacts:
                errors.append(f"Source artifact {rel.source_artifact_id} not found for relationship {rel.relationship_id}")
                
            if not rel.target_artifact_id.startswith("unresolved:"):
                if rel.target_artifact_id not in self.artifacts:
                    errors.append(f"Resolved target artifact {rel.target_artifact_id} not found for relationship {rel.relationship_id}")
                    
        return errors

    def print_statistics(self) -> None:
        print("\n--- Evidence Graph Statistics ---")
        print(f"Artifact Nodes: {len(self.artifacts)}")
        print(f"Relationships: {len(self.relationships)}")
        print(f"Resolved Edges: {self.resolved_edge_count}")
        print(f"Unresolved Edges: {self.unresolved_edge_count}")
        
def load_graph(artifacts_data: list[dict], relationships_data: list[dict]) -> EvidenceGraph:
    graph = EvidenceGraph()
    
    for art_dict in artifacts_data:
        graph.add_artifact(Artifact.model_validate(art_dict))
        
    for rel_dict in relationships_data:
        graph.add_relationship(Relationship.model_validate(rel_dict))
        
    return graph
