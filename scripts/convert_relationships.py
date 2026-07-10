import json
from pathlib import Path
from typing import Any
from collections import defaultdict

from app.models.relationships import Relationship
from scripts.analyze_github_dataset import load_github_dataset, analyze_relationships, deduplicate_relationships

def map_artifact_id(artifact_type: str, artifact_id: str, repository: str) -> str:
    """Map raw type and ID to a Universal Artifact ID or unresolved ID."""
    if artifact_type in ["issue", "pull_request", "commit"]:
        return f"github:{repository}:{artifact_type}:{artifact_id}"
    elif artifact_type == "unresolved_github_number":
        return f"unresolved:github:{repository}:number:{artifact_id}"
    return f"unknown:{artifact_type}:{artifact_id}"

def main():
    repository = "backstage/backstage"
    print(f"Loading raw dataset for {repository}...")
    dataset = load_github_dataset("backstage", "backstage")
    
    print("Extracting deterministic relationships...")
    raw_relationships = analyze_relationships(dataset)
    raw_count = len(raw_relationships)
    
    # Deduplicate exact raw relationships to avoid unnecessary duplicate processing
    # but we will also handle logic duplicates when converting.
    unique_raw = deduplicate_relationships(raw_relationships)
    print(f"Raw relationships: {raw_count}, After raw deduplication: {len(unique_raw)}")

    converted_relationships = {}
    resolved_count = 0
    unresolved_count = 0
    duplicate_count = 0
    dropped_count = 0
    conflicts = []

    for raw in unique_raw:
        try:
            source_id = map_artifact_id(raw["source_type"], raw["source_id"], repository)
            target_id = map_artifact_id(raw["target_type"], raw["target_id"], repository)
            
            # Combine evidence if there's multiple (deduplication)
            evidence_text = raw.get("evidence_text")
            
            metadata = {
                "evidence_source": raw.get("evidence_source"),
                "evidence_url": raw.get("evidence_url")
            }
            
            rel = Relationship(
                source_artifact_id=source_id,
                target_artifact_id=target_id,
                relationship_type=raw["relationship_type"],
                method="deterministic",
                evidence=evidence_text,
                confidence=1.0,
                metadata=metadata
            )
            
            # Check for logical duplicates
            if rel.relationship_id in converted_relationships:
                duplicate_count += 1
                existing_rel = converted_relationships[rel.relationship_id]
                
                # Append evidence source
                existing_sources = existing_rel.metadata.get("aggregated_sources", [existing_rel.metadata.get("evidence_source")])
                existing_sources.append(metadata.get("evidence_source"))
                existing_rel.metadata["aggregated_sources"] = list(set(existing_sources))
                
                # Append evidence text if different
                if evidence_text and evidence_text != existing_rel.evidence:
                    existing_text = existing_rel.evidence or ""
                    existing_rel.evidence = existing_text + "\n\n--- ADDITIONAL EVIDENCE ---\n\n" + evidence_text
                    
                continue
                
            converted_relationships[rel.relationship_id] = rel
            
            if raw["target_type"] == "unresolved_github_number":
                unresolved_count += 1
            else:
                resolved_count += 1
                
        except Exception as e:
            dropped_count += 1
            print(f"Dropped record due to error: {e}")

    converted_list = list(converted_relationships.values())
    
    print("\n--- Relationship Conversion Summary ---")
    print(f"Raw relationships: {raw_count}")
    print(f"Converted relationships: {len(converted_list)}")
    print(f"Resolved relationships: {resolved_count}")
    print(f"Unresolved relationships: {unresolved_count}")
    print(f"Duplicate logical relationships merged: {duplicate_count}")
    print(f"Dropped relationships: {dropped_count}")
    print(f"Conflicts: {len(conflicts)}")
    
    output_path = Path("data/normalized/github/backstage/backstage/relationships.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([rel.model_dump(mode="json") for rel in converted_list], f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved to {output_path}")
    
    # Reload validation
    with output_path.open("r", encoding="utf-8") as f:
        reloaded_data = json.load(f)
        
    for idx, item in enumerate(reloaded_data):
        try:
            Relationship.model_validate(item)
        except Exception as e:
            print(f"Validation failed on reload for item {idx}: {e}")
            break
    else:
        print("Reload validation passed successfully.")

if __name__ == "__main__":
    main()
