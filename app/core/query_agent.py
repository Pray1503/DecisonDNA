from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.memory import DecisionMemory
from app.core.graph import EvidenceGraph


class QueryAgent:
    """
    Query Agent for DecisionDNA.
    Answers natural language queries about architectural choices and engineering
    history by searching stored structured decisions and traversing the evidence graph.
    """

    def __init__(
        self,
        db_path: Path = Path("data/decision_memory.db"),
        artifacts_path: Path = Path("data/normalized/artifacts.jsonl"),
        relationships_path: Path = Path("data/normalized/relationships.jsonl"),
    ):
        self.memory = DecisionMemory(db_path=db_path)
        self.graph = EvidenceGraph()
        if artifacts_path.exists() and relationships_path.exists():
            self.graph.load_from_files(artifacts_path, relationships_path)
        else:
            self.graph.load_from_db(db_path)

    def query(self, user_query: str) -> str:
        """
        Processes a user query and returns a markdown response grounded in decisions
        and graph evidence.
        """
        # Step 1: Search reconstructed decisions table in SQLite
        matching_decisions = self.memory.search_decisions(user_query)

        if matching_decisions:
            # Present the best/first matching decision
            dec = matching_decisions[0]
            return self._format_decision_response(dec, len(matching_decisions))

        # Step 2: Traverse graph if no direct decision found
        return self._traverse_graph_for_query(user_query)

    def _format_decision_response(self, dec: Any, match_count: int) -> str:
        """
        Formats a reconstructed Decision object into a structured markdown report.
        """
        response_parts = []
        
        if match_count > 1:
            response_parts.append(
                f"> [!NOTE]\n"
                f"> Found {match_count} matching decisions. Showing the most relevant match.\n"
            )

        response_parts.append(f"# reconstructed decision: {dec.title}\n")
        response_parts.append(f"**Status/Outcome**: {dec.outcomes}\n")
        response_parts.append(f"**Confidence Score**: `{dec.confidence:.2f}`\n")
        response_parts.append(f"## Problem Statement\n{dec.problem}\n")
        response_parts.append(f"## Context & Trigger\n{dec.context}\n")
        response_parts.append(f"## Technical Decision\n{dec.decision}\n")
        response_parts.append(f"## Rationale & Reasoning\n{dec.reasoning}\n")
        
        if dec.alternatives and dec.alternatives != "No alternatives considered.":
            response_parts.append(f"## Alternatives Considered\n{dec.alternatives}\n")
            
        response_parts.append(f"## Implementation Trace\n{dec.implementation}\n")
        response_parts.append(f"## Operational Consequences & Lessons\n{dec.lessons}\n")

        # Gather details of the evidence artifacts
        evidence_artifacts = []
        for art_id in dec.evidence_ids:
            art = self.graph.get_artifact(art_id)
            if art:
                evidence_artifacts.append(art)

        response_parts.append("## Evidence Grounding")
        response_parts.append(
            f"This decision was reconstructed by traversing a connected component of **{len(dec.evidence_ids)} artifacts** in the Evidence Graph:\n"
        )

        # List by type
        adr_items = [a for a in evidence_artifacts if a.source_type == "adr"]
        issue_items = [a for a in evidence_artifacts if a.source_type == "issue"]
        pr_items = [a for a in evidence_artifacts if a.source_type == "pull_request"]
        commit_items = [a for a in evidence_artifacts if a.source_type == "commit"]

        if adr_items:
            response_parts.append(f"### Architectural Design Records:")
            for a in adr_items:
                response_parts.append(f"- `[{a.source.upper()}]` {a.external_id}: \"{a.title}\"")
        
        if issue_items:
            response_parts.append(f"### Tracked Issues:")
            for i in issue_items[:10]:
                response_parts.append(f"- `[{i.source.upper()}]` {i.external_id}: \"{i.title}\"")
            if len(issue_items) > 10:
                response_parts.append(f"- *...and {len(issue_items) - 10} more issues*")
                
        if pr_items:
            response_parts.append(f"### Pull Requests:")
            for p in pr_items[:10]:
                response_parts.append(f"- `[{p.source.upper()}]` {p.external_id}: \"{p.title}\"")
            if len(pr_items) > 10:
                response_parts.append(f"- *...and {len(pr_items) - 10} more pull requests*")

        if commit_items:
            response_parts.append(f"### Associated Commits:")
            response_parts.append(f"- Total of {len(commit_items)} commits mapped across repositories.")

        return "\n".join(response_parts)

    def _traverse_graph_for_query(self, user_query: str) -> str:
        """
        Traverses the graph to find any raw artifacts matching query keywords
        and builds a context-grounded response.
        """
        query_words = set(user_query.lower().split())
        # Filter out common short words
        stop_words = {"why", "did", "the", "choose", "what", "is", "a", "for", "to", "in", "on", "how"}
        search_words = query_words.difference(stop_words)

        if not search_words:
            return f"No evidence found in decision memory for query: '{user_query}'"

        # Search artifacts for matching keywords
        matching_artifacts = []
        for art_id, art in self.graph.artifacts.items():
            title_lower = art.title.lower()
            content_lower = art.content.lower()
            matches = [w for w in search_words if w in title_lower or w in content_lower]
            if len(matches) >= 2 or (len(matches) >= 1 and art.source_type == "adr"):
                matching_artifacts.append((art, len(matches)))

        # Sort by match counts descending
        matching_artifacts.sort(key=lambda x: x[1], reverse=True)

        if not matching_artifacts:
            return (
                f"No structured decisions or direct evidence found in the DecisionDNA database matching: "
                f"'{user_query}'."
            )

        # Get connected cluster for the best match
        best_art, _ = matching_artifacts[0]
        cluster_ids = self.graph.get_connected_cluster(best_art.artifact_id, directed=False, cutoff=2)

        response_parts = []
        response_parts.append(
            f"> [!WARNING]\n"
            f"> No structured decision directly matched your query. However, I located relevant raw engineering evidence in the graph.\n"
        )
        response_parts.append(f"# Evidence Trace: \"{best_art.title}\"")
        response_parts.append(f"Found related **{best_art.source_type.upper()}** `{best_art.external_id}` authored by @{best_art.author}.\n")
        response_parts.append(f"## Original Content Description\n{best_art.content[:600]}...\n")
        
        response_parts.append(f"## Connected Context Cluster")
        response_parts.append(
            f"This artifact is part of a connected component of **{len(cluster_ids)} artifacts** in the Evidence Graph. "
            f"This cluster contains details of related implementation work:\n"
        )

        # Summarize types
        cluster_arts = [self.graph.get_artifact(cid) for cid in cluster_ids if self.graph.get_artifact(cid)]
        types: dict = {}
        for a in cluster_arts:
            types[a.source_type] = types.get(a.source_type, 0) + 1

        for stype, count in types.items():
            response_parts.append(f"- **{count} {stype.upper()}(s)**")

        response_parts.append("\nTo reconstruct a structured decision for this cluster, please add corresponding design documentation (ADRs) to seed the decision extractor.")

        return "\n".join(response_parts)
