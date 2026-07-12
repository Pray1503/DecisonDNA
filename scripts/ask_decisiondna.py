import json
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from app.evidence.graph import load_graph
from app.evidence.retrieval import retrieve_evidence, format_evidence_package
from app.llm.provider import reconstruct_decision

def ask_pipeline(question: str, repository: str = "backstage/backstage"):
    owner, repo_name = repository.split("/")

    artifacts_path = Path(f"data/normalized/github/{owner}/{repo_name}/artifacts.json")
    rels_path = Path(f"data/normalized/github/{owner}/{repo_name}/relationships.json")

    if not artifacts_path.exists() or not rels_path.exists():
        raise FileNotFoundError("Normalized dataset not found. Please run normalizer and relationship converter first.")

    with artifacts_path.open("r", encoding="utf-8") as f:
        artifacts_data = json.load(f)

    with rels_path.open("r", encoding="utf-8") as f:
        rels_data = json.load(f)

    graph = load_graph(artifacts_data, rels_data)

    retrieval_result = retrieve_evidence(question, graph, top_k=5, max_total_chars=15000)
    package = format_evidence_package(retrieval_result)

    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is not set in environment or .env file.")

    decision = reconstruct_decision(question, package)

    # Collect actual evidence objects for UI display
    supported_artifacts = []
    if decision.evidence_artifact_ids:
        for aid in decision.evidence_artifact_ids:
            art = graph.get_artifact(aid)
            if art:
                # Find reason if it was retrieved directly
                reason = "Graph Expansion"
                for p_art in package["artifacts"]:
                    if p_art["artifact_id"] == aid:
                        reason = p_art.get("retrieval_reason", "Direct match")
                        break

                supported_artifacts.append({
                    "artifact_id": art.artifact_id,
                    "artifact_type": art.artifact_type.value,
                    "title": art.title,
                    "url": art.url,
                    "reason": reason
                })

    return {
        "reconstruction": decision.model_dump(),
        "package": package,
        "supported_artifacts": supported_artifacts,
        "graph_stats": {
            "nodes": len(graph.artifacts),
            "edges": graph.resolved_edge_count
        }
    }

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ask DecisionDNA an evidence-grounded question.")
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--repo", default="backstage/backstage", help="Repository to query")
    args = parser.parse_args()

    try:
        result = ask_pipeline(args.question, args.repo)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    decision_dict = result["reconstruction"]
    package = result["package"]

    print(f"\n--- Selected Evidence ({len(package['artifacts'])} Artifacts, {len(package['relationships'])} Relationships) ---")
    for art in package["artifacts"]:
        print(f"Artifact: {art['artifact_id']} | Type: {art['artifact_type']} | Reason: {art.get('retrieval_reason', 'Unknown')}")

    for rel in package["relationships"]:
        print(f"Relationship: {rel['source_artifact_id']} -> {rel['target_artifact_id']} ({rel['relationship_type']})")

    print("\n============================================================")
    print("DECISION RECONSTRUCTION RESULT")
    print("============================================================")

    print(f"\nANSWER:\n{decision_dict['answer']}")

    if decision_dict.get('decision'):
        print(f"\nDECISION:\n{decision_dict['decision']}")

    print(f"\nREASONING SUMMARY:\n{decision_dict['reasoning_summary']}")

    if decision_dict.get('alternatives'):
        print(f"\nALTERNATIVES CONSIDERED:\n" + "\n".join(f"- {a}" for a in decision_dict['alternatives']))

    if decision_dict.get('implementation_evidence'):
        print(f"\nIMPLEMENTATION:\n{decision_dict['implementation_evidence']}")

    if decision_dict.get('outcome'):
        print(f"\nOUTCOME:\n{decision_dict['outcome']}")

    print(f"\nEVIDENCE CHAIN:\n{decision_dict['evidence_chain']}")

    print(f"\nCONFIDENCE: {decision_dict['confidence']}")
    if decision_dict.get('uncertainty'):
        print(f"UNCERTAINTY: {decision_dict['uncertainty']}")

    if decision_dict.get('insufficient_evidence'):
        print("\n[WARNING] INSUFFICIENT EVIDENCE: The LLM indicated that the supplied evidence was insufficient to confidently answer the question.")

    print("\nSUPPORTING ARTIFACTS:")
    supported = result["supported_artifacts"]
    if not supported:
        print("  None cited.")
    else:
        for art in supported:
            print(f"  - {art['artifact_id']} | {art['artifact_type'].upper()} | {art['url']}")

if __name__ == "__main__":
    main()
