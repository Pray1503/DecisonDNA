from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.memory import DecisionMemory
from app.core.graph import EvidenceGraph
from app.core.llm import LLMProvider


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
        self.llm = LLMProvider()

    def query(self, user_query: str) -> str:
        """
        Processes a user query and returns a markdown response grounded in decisions
        and graph evidence.
        """
        # Step 1: Search reconstructed decisions table in SQLite
        matching_decisions = self.memory.search_decisions(user_query)

        # Step 2: Search artifacts in the graph
        query_words = set(user_query.lower().split())
        stop_words = {"why", "did", "the", "choose", "what", "is", "a", "for", "to", "in", "on", "how", "we", "they", "should", "use"}
        search_words = query_words.difference(stop_words)

        matching_artifacts = []
        if search_words:
            for art_id, art in self.graph.artifacts.items():
                title_lower = art.title.lower()
                content_lower = art.content.lower()
                matches = [w for w in search_words if w in title_lower or w in content_lower]
                if len(matches) >= 2 or (len(matches) >= 1 and art.source_type == "adr"):
                    matching_artifacts.append((art, len(matches)))
            matching_artifacts.sort(key=lambda x: x[1], reverse=True)

        # Step 3: Build context for LLM
        context_parts = []
        if matching_decisions:
            context_parts.append("### Relevant Reconstructed Decisions:")
            for idx, dec in enumerate(matching_decisions[:5]):
                context_parts.append(
                    f"Decision {idx+1}: {dec.title}\n"
                    f"- Problem: {dec.problem}\n"
                    f"- Context: {dec.context}\n"
                    f"- Chosen Solution: {dec.decision}\n"
                    f"- Rationale: {dec.reasoning}\n"
                    f"- Implementation: {dec.implementation}\n"
                    f"- Outcomes: {dec.outcomes}\n"
                    f"- Lessons: {dec.lessons}\n"
                    f"- Confidence Score: {dec.confidence:.2f}\n"
                )
                
                # Fetch details of evidence artifacts linked to this decision to provide code/incident level details
                if dec.evidence_ids:
                    context_parts.append(f"Evidence Artifacts for Decision {idx+1}:")
                    for art_id in dec.evidence_ids[:8]:
                        art = self.graph.get_artifact(art_id)
                        if art:
                            context_parts.append(
                                f"  - [{art.source_type.upper()}] {art.external_id} - \"{art.title}\"\n"
                                f"    Author: @{art.author}\n"
                                f"    Source System: {art.source}\n"
                                f"    Timestamps: {art.timestamps}\n"
                                f"    Context (Repo/Branch): {art.context}\n"
                                f"    Metadata: {art.metadata}\n"
                                f"    Content/Details: {art.content[:1500]}\n"
                            )

        if matching_artifacts:
            context_parts.append("### Relevant Engineering Evidence / Artifacts:")
            for idx, (art, matches) in enumerate(matching_artifacts[:8]):
                context_parts.append(
                    f"Artifact {idx+1}: [{art.source_type.upper()}] {art.external_id} - \"{art.title}\"\n"
                    f"- Author: @{art.author}\n"
                    f"- Source System: {art.source}\n"
                    f"- Timestamps: {art.timestamps}\n"
                    f"- Context (Repo/Branch): {art.context}\n"
                    f"- Metadata: {art.metadata}\n"
                    f"- Content/Details: {art.content[:1500]}\n"
                )

            # If no decisions match but we have matching artifacts, fetch cluster details for the best match
            if not matching_decisions and matching_artifacts:
                best_art, _ = matching_artifacts[0]
                cluster_ids = self.graph.get_connected_cluster(best_art.artifact_id, directed=False, cutoff=2)
                cluster_arts = [self.graph.get_artifact(cid) for cid in cluster_ids if self.graph.get_artifact(cid)]
                context_parts.append(f"\n### Connected Context Cluster for Best Match \"{best_art.title}\":")
                context_parts.append(f"This artifact is part of a connected component of {len(cluster_ids)} artifacts.")
                types: dict = {}
                for a in cluster_arts:
                    types[a.source_type] = types.get(a.source_type, 0) + 1
                    # Log details of important nodes in cluster
                    if len(context_parts) < 30 and a.source_type in ["commit", "incident", "issue"]:
                        context_parts.append(
                            f"  - Cluster Node: [{a.source_type.upper()}] {a.external_id} - \"{a.title}\"\n"
                            f"    Author: @{a.author}\n"
                            f"    Context: {a.context}\n"
                            f"    Metadata: {a.metadata}\n"
                            f"    Content/Details: {a.content[:1500]}\n"
                        )
                for stype, count in types.items():
                    context_parts.append(f"- {count} {stype.upper()}(s)")

        context_str = "\n".join(context_parts) if context_parts else "No direct matching architectural decisions or engineering evidence found in the database."

        # Step 4: Call LLM with the context and query
        prompt = f"""You are the DecisionDNA AI Assistant, a friendly and helpful software engineering advisor.
Your goal is to answer the user's natural language queries about architectural choices, system designs, project history, and engineering decisions.

You must answer the question like a normal, conversational, and helpful person.
Avoid sounding overly mechanical. Integrate technical details, reasoning, and context naturally.
Use professional, friendly, and clear Markdown formatting.

User Query:
"{user_query}"

Architectural Context retrieved from Decision Memory (SQLite database & Evidence Graph):
{context_str}

Guidelines for your response:
1. If the query is a simple greeting or general/conversational question (e.g. "hello", "who are you", "how are you"), respond in a warm, welcoming, and helpful manner, introducing yourself as the DecisionDNA assistant.
2. If context is provided, ground your answer in that context. Explain the background/problem, the technical decisions made, why they were chosen, and their outcomes. Use bullet points or sections where appropriate, but make the flow natural and cohesive.
3. Be highly detailed, specific, and technical. If the retrieved context contains exact file names, branch names, commit hashes, JIRA ticket numbers, line numbers, or specific error trace messages, you MUST include them precisely in your response (e.g., 'An error occurred in line 498 during commit 56'). Do not summarize, omit, or genericize these concrete details.
4. If the user asks about engineering choices that aren't in the provided context, state politely that you couldn't find specific evidence for it in the active decision memory, but offer general insights if relevant or ask them to specify project names or technologies.
5. Do not mention "database queries", "SQLite", "artifacts in the graph", or "context_str" directly in your response unless asked about how the tool works. Talk to the user naturally about the system's design and decision history.

Please write your conversational response below:
"""

        try:
            response = self.llm.generate_text(prompt)
            if response:
                return response
        except Exception as e:
            print(f"Error calling LLM provider: {e}")
            q_lower = user_query.lower()
            if any(w in q_lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]):
                return "Hello! I am your DecisionDNA AI assistant. How can I help you trace architectural decisions or explore engineering evidence today?"
            elif any(w in q_lower for w in ["who are you", "what is your name", "identify yourself"]):
                return "I am DecisionDNA AI, a decision intelligence agent trained to trace technical architectural decisions across your developer ecosystem."

        # Fallback behaviour if LLM fails or is not configured
        if matching_decisions:
            dec = matching_decisions[0]
            return self._format_decision_response(dec, len(matching_decisions))

        # Step 5: Traverse graph if no direct decision found
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
