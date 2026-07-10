import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.graph import EvidenceGraph
from app.core.llm import LLMProvider
from app.core.memory import DecisionMemory
from app.models.decision import Decision


def main():
    artifacts_file = Path("data/normalized/artifacts.jsonl")
    relationships_file = Path("data/normalized/relationships.jsonl")
    db_file = Path("data/decision_memory.db")

    if not artifacts_file.exists() or not relationships_file.exists():
        print("ERROR: Normalized files do not exist. Run ingestion and extraction first.")
        sys.exit(1)

    print("Initializing EvidenceGraph...")
    eg = EvidenceGraph()
    eg.load_from_files(artifacts_file, relationships_file)

    print("Initializing LLMProvider and DecisionMemory database...")
    llm = LLMProvider()
    memory = DecisionMemory(db_path=db_file)

    # --------------------------------------------------
    # 1. LOAD ALL ARTIFACTS AND RELATIONSHIPS TO SQLITE
    # --------------------------------------------------
    print("\nLoading raw artifacts and relationships into SQLite tables...")
    memory.save_artifacts_batch(list(eg.artifacts.values()))
    memory.save_relationships_batch(list(eg.relationships.values()))
    print(f"Loaded {len(eg.artifacts)} artifacts and {len(eg.relationships)} relationships into SQLite.")

    # --------------------------------------------------
    # 2. IDENTIFY SEED ADRs AND RUN RECONSTRUCTION
    # --------------------------------------------------
    # Find all ADRs
    adr_nodes = [
        node_id 
        for node_id, art in eg.artifacts.items() 
        if art.source_type == "adr"
    ]

    print(f"\nDiscovered {len(adr_nodes)} seed ADRs in graph. Starting decision reconstruction...")

    decisions_to_save: List[Decision] = []

    for idx, adr_id in enumerate(adr_nodes, 1):
        adr = eg.get_artifact(adr_id)
        if not adr:
            continue

        print(f"[{idx}/{len(adr_nodes)}] Reconstructing decision for seed {adr.external_id}...")

        # Find connected evidence component (undirected traversal)
        cluster_ids = eg.get_connected_cluster(adr_id, directed=False, cutoff=2)
        cluster_artifacts = [eg.get_artifact(cid) for cid in cluster_ids if eg.get_artifact(cid)]

        # Compile cluster details text representation
        evidence_lines = []
        for art in cluster_artifacts:
            # Skip the seed ADR itself in the downstream evidence log
            if art.artifact_id == adr_id:
                continue
            evidence_lines.append(
                f"- [{art.source_type.upper()}] {art.external_id}: \"{art.title}\"\n"
                f"  Author: @{art.author} | Date/Time: {json.dumps(art.timestamps)}\n"
                f"  Content: {art.content[:200].replace('\n', ' ')}...\n"
            )
        cluster_text = "\n".join(evidence_lines)

        try:
            # Reconstruct structured decision fields using LLM or local mock
            result = llm.reconstruct_decision(
                adr=adr.to_dict(),
                cluster_text=cluster_text,
                connected_artifacts=[a.to_dict() for a in cluster_artifacts if a.artifact_id != adr_id]
            )

            # Generate structured Pydantic object
            decision_uuid = Decision.generate_id(adr.external_id)
            decision = Decision(
                decision_id=decision_uuid,
                title=result.get("title") or adr.title,
                problem=result.get("problem") or "No problem description.",
                context=result.get("context") or "No context description.",
                constraints=result.get("constraints") or "No constraints.",
                alternatives=result.get("alternatives") or "No alternatives considered.",
                decision=result.get("decision") or "No decision description.",
                reasoning=result.get("reasoning") or "No reasoning provided.",
                implementation=result.get("implementation") or "No implementation details.",
                outcomes=result.get("outcomes") or "No operational outcomes.",
                lessons=result.get("lessons") or "No lessons learned.",
                confidence=float(result.get("confidence", 0.9)),
                evidence_ids=list(cluster_ids)
            )

            decisions_to_save.append(decision)
        except Exception as e:
            print(f"ERROR: Failed to reconstruct decision for {adr.external_id}: {e}")

    if decisions_to_save:
        print(f"\nSaving {len(decisions_to_save)} reconstructed decisions to SQLite in a single transaction...")
        memory.save_decisions_batch(decisions_to_save)

    print("\n--------------------------------------------------")
    print(f"DECISION RECONSTRUCTION COMPLETE!")
    print(f"  - Reconstructed and stored: {len(decisions_to_save)} decisions")
    print(f"  - SQLite Database populated at: {db_file}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
