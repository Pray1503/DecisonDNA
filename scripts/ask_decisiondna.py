import json
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from app.evidence.graph import load_graph
from app.evidence.retrieval import retrieve_evidence, format_evidence_package
from app.llm.provider import reconstruct_decision

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Ask DecisionDNA an evidence-grounded question.")
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--repo", default="backstage/backstage", help="Repository to query")
    args = parser.parse_args()
    
    question = args.question
    repository = args.repo
    owner, repo_name = repository.split("/")
    
    artifacts_path = Path(f"data/normalized/github/{owner}/{repo_name}/artifacts.json")
    rels_path = Path(f"data/normalized/github/{owner}/{repo_name}/relationships.json")
    
    if not artifacts_path.exists() or not rels_path.exists():
        print("Normalized dataset not found. Please run normalizer and relationship converter first.")
        sys.exit(1)
        
    print("Loading Evidence Graph...")
    with artifacts_path.open("r", encoding="utf-8") as f:
        artifacts_data = json.load(f)
        
    with rels_path.open("r", encoding="utf-8") as f:
        rels_data = json.load(f)
        
    graph = load_graph(artifacts_data, rels_data)
    graph.print_statistics()
    
    print(f"\nQuestion: {question}")
    print("\nRetrieving candidates and expanding evidence...")
    
    # Retrieve
    retrieval_result = retrieve_evidence(question, graph, top_k=5, max_total_chars=15000)
    
    # Package
    package = format_evidence_package(retrieval_result)
    
    print(f"\n--- Selected Evidence ({len(package['artifacts'])} Artifacts, {len(package['relationships'])} Relationships) ---")
    for art in package["artifacts"]:
        print(f"Artifact: {art['artifact_id']} | Type: {art['artifact_type']} | Reason: {art['retrieval_reason']}")
        
    for rel in package["relationships"]:
        print(f"Relationship: {rel['source_artifact_id']} -> {rel['target_artifact_id']} ({rel['relationship_type']})")
        
    if not os.environ.get("GROQ_API_KEY"):
        print("\n[STOP] GROQ_API_KEY is not set in environment or .env file.")
        print("Please set GROQ_API_KEY to proceed with the LLM phase.")
        sys.exit(1)
        
    print("\nCalling Groq LLM for Decision Reconstruction...")
    try:
        decision = reconstruct_decision(question, package)
    except Exception as e:
        print(f"\n[ERROR] LLM Reconstruction Failed: {e}")
        sys.exit(1)
        
    print("\n============================================================")
    print("DECISION RECONSTRUCTION RESULT")
    print("============================================================")
    
    print(f"\nANSWER:\n{decision.answer}")
    
    if decision.decision:
        print(f"\nDECISION:\n{decision.decision}")
        
    print(f"\nREASONING SUMMARY:\n{decision.reasoning_summary}")
    
    if decision.alternatives:
        print(f"\nALTERNATIVES CONSIDERED:\n" + "\n".join(f"- {a}" for a in decision.alternatives))
        
    if decision.implementation_evidence:
        print(f"\nIMPLEMENTATION:\n{decision.implementation_evidence}")
        
    if decision.outcome:
        print(f"\nOUTCOME:\n{decision.outcome}")
        
    print(f"\nEVIDENCE CHAIN:\n{decision.evidence_chain}")
    
    print(f"\nCONFIDENCE: {decision.confidence}")
    if decision.uncertainty:
        print(f"UNCERTAINTY: {decision.uncertainty}")
        
    if decision.insufficient_evidence:
        print("\n[WARNING] INSUFFICIENT EVIDENCE: The LLM indicated that the supplied evidence was insufficient to confidently answer the question.")
        
    print("\nSUPPORTING ARTIFACTS:")
    if not decision.evidence_artifact_ids:
        print("  None cited.")
    else:
        for aid in decision.evidence_artifact_ids:
            art = graph.get_artifact(aid)
            if art:
                print(f"  - {aid} | {art.artifact_type.value.upper()} | {art.url}")
            else:
                print(f"  - {aid} | UNKNOWN")

if __name__ == "__main__":
    main()
