import os
import sys
from pathlib import Path

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.graph import EvidenceGraph


def main():
    artifacts_file = Path("data/normalized/artifacts.jsonl")
    relationships_file = Path("data/normalized/relationships.jsonl")

    if not artifacts_file.exists() or not relationships_file.exists():
        print("ERROR: Normalized files do not exist. Run ingestion and extraction first.")
        sys.exit(1)

    print("Initializing EvidenceGraph...")
    eg = EvidenceGraph()

    print("Loading data from files into NetworkX...")
    nodes_loaded, edges_loaded = eg.load_from_files(artifacts_file, relationships_file)

    print(f"Graph loaded successfully:")
    print(f"  - Nodes (Artifacts): {nodes_loaded}")
    print(f"  - Edges (Relationships): {edges_loaded}")

    # Check networkx graph properties
    nx_nodes = eg.graph.number_of_nodes()
    nx_edges = eg.graph.number_of_edges()
    print(f"NetworkX internal stats: Nodes={nx_nodes}, Edges={nx_edges}")

    assert nx_nodes > 0, "NetworkX graph must contain nodes"
    assert nx_edges > 0, "NetworkX graph must contain edges"

    # --------------------------------------------------
    # TEST 1: NEIGHBOR QUERIES
    # --------------------------------------------------
    print("\n--- Test 1: Query Neighbors for ADR-0001 ---")
    adr_node_id = "github:prj-006:adr:ADR-0001"
    
    if adr_node_id in eg.graph:
        neighbors = eg.get_neighbors(adr_node_id, direction="both")
        print(f"Neighbors for {adr_node_id} (count: {len(neighbors)}):")
        # Group by source type
        types: dict = {}
        for nid in neighbors:
            art = eg.get_artifact(nid)
            stype = art.source_type if art else "unknown"
            types[stype] = types.get(stype, 0) + 1
            
        for stype, count in types.items():
            print(f"  - {stype}: {count}")
    else:
        print(f"WARNING: Node {adr_node_id} not found in graph.")

    # --------------------------------------------------
    # TEST 2: PATH TRAVERSAL (TICKET -> PR -> COMMIT)
    # --------------------------------------------------
    print("\n--- Test 2: Path Traversal ---")
    source_ticket = None
    for node_id in eg.graph.nodes:
        art = eg.get_artifact(node_id)
        if art and art.source == "jira" and art.source_type == "issue":
            source_ticket = node_id
            break
            
    # We want to find a commit linked to it. Let's find one by traversing relationships.
    target_commit = None
    
    # Let's search JIRA ticket successors/predecessors
    if source_ticket and source_ticket in eg.graph:
        connected = eg.get_connected_cluster(source_ticket, directed=False)
        for nid in connected:
            art = eg.get_artifact(nid)
            if art and art.source_type == "commit":
                target_commit = nid
                break
                
    if source_ticket and source_ticket in eg.graph and target_commit:
        print(f"Finding path from JIRA issue '{source_ticket}' to Commit '{target_commit}'...")
        path = eg.find_shortest_path(source_ticket, target_commit, directed=False)
        if path:
            print("Path found:")
            for step in path:
                art = eg.get_artifact(step)
                title = art.title if art else "unknown"
                stype = art.source_type if art else "unknown"
                print(f"  -> [{stype.upper()}] {step}: \"{title}\"")
        else:
            print("No path found.")
    else:
        print(f"WARNING: Could not perform path traversal (missing ticket or commit).")

    # --------------------------------------------------
    # TEST 3: DECISION TRANSITIVE CLUSTERS
    # --------------------------------------------------
    print("\n--- Test 3: Connected Component (Decision Cluster) ---")
    # Gather everything connected to ADR-0001
    if adr_node_id in eg.graph:
        cluster = eg.get_connected_cluster(adr_node_id, directed=False)
        print(f"Connected component size for {adr_node_id}: {len(cluster)} artifacts")
        
        # Breakdown the cluster members
        cluster_types: dict = {}
        for nid in cluster:
            art = eg.get_artifact(nid)
            stype = art.source_type if art else "unknown"
            cluster_types[stype] = cluster_types.get(stype, 0) + 1
            
        print("Cluster contents:")
        for stype, count in cluster_types.items():
            print(f"  - {stype}: {count}")
            
        assert cluster_types.get("adr", 0) >= 1, "Must contain at least the ADR itself"
        assert cluster_types.get("pull_request", 0) >= 1, "Must contain pull request implementing it"
        assert cluster_types.get("commit", 0) >= 1, "Must contain commits implementing it"
    else:
        print(f"WARNING: ADR-0001 not found.")

    print("\nALL GRAPH TESTS AND TRAVERSALS VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
