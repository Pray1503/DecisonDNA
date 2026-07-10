import json
import re
from pathlib import Path
from collections import defaultdict, Counter

from app.models.artifacts import Artifact
from scripts.analyze_github_dataset import load_github_dataset, analyze_relationships, deduplicate_relationships

def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    stop_words = {"the", "and", "for", "with", "that", "this", "are", "from", "can", "not", "use", "has", "but", "have"}
    return set(words) - stop_words

def score_overlap(doc_text: str, artifact_text: str) -> float:
    if not doc_text or not artifact_text:
        return 0.0
    doc_tokens = tokenize(doc_text)
    art_tokens = tokenize(artifact_text)
    if not doc_tokens:
        return 0.0
    overlap = len(doc_tokens.intersection(art_tokens))
    return overlap / len(doc_tokens)

def main():
    print("Loading normalized artifacts...")
    artifacts_path = Path("data/normalized/github/backstage/backstage/artifacts.json")
    with artifacts_path.open("r", encoding="utf-8") as f:
        artifacts_data = json.load(f)
    
    artifacts = [Artifact.model_validate(a) for a in artifacts_data]
    artifacts_by_id = {a.artifact_id: a for a in artifacts}
    
    print(f"Loaded {len(artifacts)} artifacts.")

    print("Extracting deterministic relationships...")
    raw_dataset = load_github_dataset("backstage", "backstage")
    raw_rels = analyze_relationships(raw_dataset)
    raw_rels = deduplicate_relationships(raw_rels)
    print(f"Extracted {len(raw_rels)} relationships.")

    # Build graph
    adj = defaultdict(list)
    for rel in raw_rels:
        src = f"github:backstage/backstage:{rel['source_type']}:{rel['source_id']}"
        tgt = rel["target_id"]
        tgt_type = rel.get("target_type")
        if tgt_type in ["issue", "pull_request", "commit"]:
            tgt = f"github:backstage/backstage:{tgt_type}:{tgt}"
        elif tgt_type == "unresolved_github_number":
            tgt = f"unresolved:#{tgt}"
        
        adj[src].append((tgt, rel["relationship_type"]))

    documents = [a for a in artifacts if a.artifact_type.value == "document"]
    other_artifacts = [a for a in artifacts if a.artifact_type.value != "document"]

    print("Analyzing semantic overlap with ADRs...")
    doc_connections = defaultdict(list)
    
    for doc in documents:
        doc_text = f"{doc.title} {doc.content}"
        for art in other_artifacts:
            art_text = f"{art.title} {art.content}"
            score = score_overlap(doc_text, art_text)
            if score > 0.15: # Arbitrary threshold for reasonable overlap
                doc_connections[doc.artifact_id].append((art.artifact_id, score))

    print("\n--- Evidence Coverage Probe Results ---\n")
    
    # We evaluate specific candidates mentioned and others
    candidates = []

    # 1. Luxon
    luxon_doc = next((d for d in documents if "adr010-luxon" in d.external_id), None)
    luxon_related = [a for a in other_artifacts if "luxon" in (a.content or "").lower() or "luxon" in (a.title or "").lower()]
    if luxon_doc and luxon_related:
        candidates.append({
            "question": "Why did Backstage choose Luxon as its date library?",
            "confidence": "HIGH" if len(luxon_related) > 2 else "MEDIUM",
            "docs": [luxon_doc.artifact_id],
            "related": [a.artifact_id for a in luxon_related],
            "explanation": "Strong candidate. ADR exists and PRs/issues discussing Luxon are present."
        })

    # 2. MSW
    msw_doc = next((d for d in documents if "adr007-use-msw" in d.external_id), None)
    msw_related = [a for a in other_artifacts if "msw" in (a.content or "").lower() or "msw" in (a.title or "").lower()]
    if msw_doc and msw_related:
        candidates.append({
            "question": "Why does Backstage use MSW for mocking?",
            "confidence": "HIGH" if len(msw_related) > 2 else "MEDIUM",
            "docs": [msw_doc.artifact_id],
            "related": [a.artifact_id for a in msw_related],
            "explanation": "ADR exists and MSW is discussed in PRs/issues."
        })

    # 3. Default exports
    exports_doc = next((d for d in documents if "adr003-avoid-default" in d.external_id), None)
    exports_related = [a for a in other_artifacts if "default export" in (a.content or "").lower() or "export default" in (a.content or "").lower()]
    if exports_doc and exports_related:
        candidates.append({
            "question": "Why does Backstage avoid default exports?",
            "confidence": "HIGH" if len(exports_related) > 1 else "MEDIUM",
            "docs": [exports_doc.artifact_id],
            "related": [a.artifact_id for a in exports_related],
            "explanation": "ADR exists, some mentions in issues/PRs."
        })

    # 4. Catalog file format
    catalog_doc = next((d for d in documents if "adr002-default-catalog" in d.external_id), None)
    catalog_related = [a for a in other_artifacts if "catalog-info" in (a.content or "").lower()]
    if catalog_doc and catalog_related:
        candidates.append({
            "question": "What is the default catalog file format and why?",
            "confidence": "HIGH" if len(catalog_related) > 1 else "MEDIUM",
            "docs": [catalog_doc.artifact_id],
            "related": [a.artifact_id for a in catalog_related],
            "explanation": "Core Backstage feature documented in ADR, heavily referenced."
        })

    # Generic check for other clusters
    for doc_id, related in doc_connections.items():
        if len(related) >= 3:
            doc = artifacts_by_id[doc_id]
            # Skip if already captured
            if any(doc_id in c["docs"] for c in candidates):
                continue
            candidates.append({
                "question": f"What was the decision regarding {doc.title}?",
                "confidence": "MEDIUM",
                "docs": [doc_id],
                "related": [r[0] for r in related],
                "explanation": f"Semantic overlap found with {len(related)} artifacts."
            })

    candidates.sort(key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["confidence"]], reverse=True)

    for i, c in enumerate(candidates[:5]):
        print(f"CANDIDATE {i+1}: {c['question']}")
        print(f"Confidence: {c['confidence']}")
        print(f"Docs: {c['docs']}")
        print(f"Related Artifacts: {len(c['related'])} (e.g. {c['related'][:3]})")
        print(f"Explanation: {c['explanation']}\n")

if __name__ == "__main__":
    main()
