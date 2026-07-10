import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.graph import EvidenceGraph
from app.core.llm import LLMProvider
from app.core.embeddings import EmbeddingService
from app.models.relationship import Relationship


def main():
    # Paths
    artifacts_file = Path("data/normalized/artifacts.jsonl")
    relationships_file = Path("data/normalized/relationships.jsonl")

    if not artifacts_file.exists() or not relationships_file.exists():
        print("ERROR: Normalized files do not exist. Run ingestion and extraction first.")
        sys.exit(1)

    print("Initializing EvidenceGraph...")
    eg = EvidenceGraph()
    eg.load_from_files(artifacts_file, relationships_file)

    print("Initializing services...")
    llm = LLMProvider()
    embedding_service = EmbeddingService()

    # --------------------------------------------------
    # GROUP ARTIFACTS BY PROJECT/REPOSITORY SCOPE
    # --------------------------------------------------
    print("\nGrouping artifacts by project scope...")
    
    # We want to compare ADRs with Issues and PRs
    # project_key -> {"adrs": [...], "targets": [...]}
    project_groups: Dict[str, Dict[str, List[Any]]] = {}

    for art_id, art in eg.artifacts.items():
        # Find project key
        proj = art.context.get("project") or art.context.get("repository") or art.context.get("repo")
        if not proj:
            continue
            
        proj_key = str(proj).strip().upper()
        if proj_key not in project_groups:
            project_groups[proj_key] = {"adrs": [], "targets": []}

        if art.source_type == "adr":
            project_groups[proj_key]["adrs"].append(art)
        elif art.source_type in ["issue", "pull_request"]:
            project_groups[proj_key]["targets"].append(art)

    print(f"Grouped artifacts into {len(project_groups)} project scopes.")

    # --------------------------------------------------
    # SEMANTIC CANDIDATE RETRIEVAL
    # --------------------------------------------------
    print("\nStarting semantic candidate retrieval...")
    SIM_THRESHOLD = 0.45
    candidates: List[Tuple[Any, Any, float]] = []

    for proj_key, group in project_groups.items():
        adrs = group["adrs"]
        targets = group["targets"]

        if not adrs or not targets:
            continue

        print(f"Project {proj_key}: Comparing {len(adrs)} ADRs with {len(targets)} Issues/PRs...")

        # Construct texts
        adr_texts = [f"Title: {a.title}\nContent: {a.content[:300]}" for a in adrs]
        target_texts = [f"Title: {t.title}\nContent: {t.content[:300]}" for t in targets]

        # Calculate similarity matrix
        sim_matrix = embedding_service.calculate_similarities(adr_texts, target_texts)

        # Find candidate pairs above threshold
        for i, adr in enumerate(adrs):
            for j, target in enumerate(targets):
                score = float(sim_matrix[i, j])
                if score >= SIM_THRESHOLD:
                    # Check if already connected in graph
                    if eg.graph.has_edge(adr.artifact_id, target.artifact_id) or \
                       eg.graph.has_edge(target.artifact_id, adr.artifact_id):
                        continue
                    candidates.append((adr, target, score))

    print(f"\nDiscovered {len(candidates)} semantic candidates above similarity threshold {SIM_THRESHOLD}.")

    # Sort candidates by score descending
    candidates.sort(key=lambda x: x[2], reverse=True)

    # --------------------------------------------------
    # LLM SEMANTIC EVALUATION
    # --------------------------------------------------
    print("\nRunning LLM evaluation on top candidates...")
    new_relationships: List[Relationship] = []
    
    # Process top candidates (e.g. limit to 100 to prevent API timeouts or excessive mock runs)
    max_evaluations = 100
    eval_count = 0

    provenance = {
        "extracted_at": "now",
        "extractor": "AISemanticAnalysisPipeline",
        "version": "1.0.0",
        "model": "gemini-1.5-flash" if llm.gemini_key else "mock",
    }

    for adr, target, score in candidates[:max_evaluations]:
        eval_count += 1
        print(f"Evaluating candidate {eval_count}/{min(len(candidates), max_evaluations)} (Score: {score:.3f}):")
        print(f"  - ADR: {adr.external_id} \"{adr.title}\"")
        print(f"  - Target: {target.source_type.upper()} {target.external_id} \"{target.title}\"")

        try:
            # Call LLM or Mock
            result = llm.evaluate_relationship(adr.to_dict(), target.to_dict())

            if result.get("related"):
                rel_type = "semantically_related"
                rel_id = Relationship.generate_id(adr.artifact_id, target.artifact_id, rel_type)
                
                confidence = float(result.get("confidence", 0.8))
                reasoning = result.get("reasoning", "LLM determined semantic connection.")

                relationship = Relationship(
                    relationship_id=rel_id,
                    source_id=adr.artifact_id,
                    target_id=target.artifact_id,
                    relationship_type=rel_type,
                    confidence=confidence,
                    reasoning=reasoning,
                    evidence={"similarity_score": score, "llm_type": result.get("relationship_type")},
                    provenance=provenance,
                )
                
                new_relationships.append(relationship)
                print(f"  --> [CONNECTED] Confidence: {confidence:.2f}. Reasoning: {reasoning}")
            else:
                print("  --> [REJECTED]")
        except Exception as e:
            print(f"  --> ERROR evaluating candidate: {e}")

    # --------------------------------------------------
    # APPEND NEW RELATIONSHIPS TO DATABASE
    # --------------------------------------------------
    if new_relationships:
        print(f"\nAppending {len(new_relationships)} new semantic relationships to {relationships_file}...")
        with open(relationships_file, "a", encoding="utf-8") as out:
            for rel in new_relationships:
                out.write(json.dumps(rel.to_dict(), ensure_ascii=False) + "\n")
    else:
        print("\nNo new semantic relationships discovered.")

    print("\n--------------------------------------------------")
    print(f"SEMANTIC PIPELINE COMPLETE! Added {len(new_relationships)} semantic relationships.")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
