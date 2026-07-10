import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from app.models.artifact import Artifact
from app.models.relationship import Relationship


class EvidenceGraph:
    """
    Evidence Graph for DecisionDNA, representing engineering evidence
    (Artifacts) as nodes and their connections (Relationships) as edges.
    Powered by NetworkX for efficient path finding and cluster traversal.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.artifacts: Dict[str, Artifact] = {}
        self.relationships: Dict[str, Relationship] = {}
        self._undirected_graph = None

    def add_artifact(self, artifact: Artifact) -> None:
        """
        Add a normalized artifact as a node in the graph.
        """
        self._undirected_graph = None
        self.artifacts[artifact.artifact_id] = artifact
        # Add or update node attributes in NetworkX
        self.graph.add_node(
            artifact.artifact_id,
            source=artifact.source,
            source_type=artifact.source_type,
            external_id=artifact.external_id,
            title=artifact.title,
            author=artifact.author,
            url=artifact.url,
            context=artifact.context,
            metadata=artifact.metadata,
        )

    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add a directed relationship as an edge in the graph.
        """
        self._undirected_graph = None
        self.relationships[relationship.relationship_id] = relationship
        
        # Verify source and target exist as nodes; add placeholder attributes if missing
        if relationship.source_id not in self.graph:
            self.graph.add_node(relationship.source_id)
        if relationship.target_id not in self.graph:
            self.graph.add_node(relationship.target_id)

        self.graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            relationship_id=relationship.relationship_id,
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
            reasoning=relationship.reasoning,
            evidence=relationship.evidence,
        )

    def load_from_files(
        self,
        artifacts_path: Path,
        relationships_path: Path,
    ) -> Tuple[int, int]:
        """
        Load artifacts and relationships from JSON Lines files.
        """
        nodes_loaded = 0
        edges_loaded = 0

        # Load artifacts
        if artifacts_path.exists():
            with open(artifacts_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        artifact = Artifact.from_dict(data)
                        self.add_artifact(artifact)
                        nodes_loaded += 1
                    except Exception as e:
                        print(f"Error parsing artifact line: {e}")
        else:
            print(f"WARNING: Artifacts file {artifacts_path} does not exist.")

        # Load relationships
        if relationships_path.exists():
            with open(relationships_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        relationship = Relationship.from_dict(data)
                        self.add_relationship(relationship)
                        edges_loaded += 1
                    except Exception as e:
                        print(f"Error parsing relationship line: {e}")
        else:
            print(f"WARNING: Relationships file {relationships_path} does not exist.")

        return nodes_loaded, edges_loaded

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """
        Retrieve Artifact object by its ID.
        """
        return self.artifacts.get(artifact_id)

    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """
        Retrieve Relationship object by its ID.
        """
        return self.relationships.get(relationship_id)

    def get_neighbors(
        self,
        artifact_id: str,
        direction: str = "both",
    ) -> List[str]:
        """
        Get neighboring node IDs of an artifact.
        
        Directions:
        - "out": Nodes this artifact points to (successors).
        - "in": Nodes pointing to this artifact (predecessors).
        - "both": Union of incoming and outgoing neighbors.
        """
        if artifact_id not in self.graph:
            return []

        if direction == "out":
            return list(self.graph.successors(artifact_id))
        elif direction == "in":
            return list(self.graph.predecessors(artifact_id))
        elif direction == "both":
            out_nodes = set(self.graph.successors(artifact_id))
            in_nodes = set(self.graph.predecessors(artifact_id))
            return list(out_nodes.union(in_nodes))
        else:
            raise ValueError(f"Invalid direction: {direction}. Use 'out', 'in', or 'both'.")

    def _get_undirected_graph(self) -> nx.Graph:
        if self._undirected_graph is None:
            self._undirected_graph = self.graph.to_undirected()
        return self._undirected_graph

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        directed: bool = False,
    ) -> Optional[List[str]]:
        """
        Find the shortest path of node IDs between source and target.
        If directed=False, allows traversing edges against their direction.
        Returns None if no path exists.
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None

        g_to_search = self.graph if directed else self._get_undirected_graph()
        try:
            return nx.shortest_path(g_to_search, source=source_id, target=target_id)
        except nx.NetworkXNoPath:
            return None

    def get_connected_cluster(
        self,
        artifact_id: str,
        directed: bool = False,
        cutoff: Optional[int] = None,
    ) -> Set[str]:
        """
        Retrieve all connected node IDs associated with the target artifact.
        Useful for gathering all evidence related to a single decision context.
        If cutoff is specified, limits the depth of the traversal.
        """
        if artifact_id not in self.graph:
            return set()

        if cutoff is not None:
            g_to_search = self.graph if directed else self._get_undirected_graph()
            return set(nx.single_source_shortest_path_length(g_to_search, artifact_id, cutoff=cutoff).keys())

        if directed:
            # Traversal along directed paths (descendants)
            return nx.descendants(self.graph, artifact_id).union({artifact_id})
        else:
            # Full connected component in undirected version
            return nx.node_connected_component(self._get_undirected_graph(), artifact_id)

    def get_subgraph(self, node_ids: List[str]) -> nx.DiGraph:
        """
        Extract a subgraph containing only the specified node IDs.
        """
        valid_nodes = [nid for nid in node_ids if nid in self.graph]
        return self.graph.subgraph(valid_nodes)
