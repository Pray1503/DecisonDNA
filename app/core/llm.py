import os
import json
import re
from typing import Any, Dict, List, Optional
import requests


class LLMProvider:
    """
    LLM Client Provider for DecisionDNA.
    Supports Gemini (Google), Groq, and OpenAI via REST APIs.
    Falls back to a keyword-matching heuristic when no API keys are present.
    """

    def __init__(self):
        # Load keys from environment
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama3-8b-8192")

        if self.gemini_key:
            print("LLMProvider: Initialized with Google Gemini API.")
        elif self.groq_key:
            print("LLMProvider: Initialized with Groq API.")
        elif self.openai_key:
            print("LLMProvider: Initialized with OpenAI API.")
        else:
            print("LLMProvider: WARNING - No API keys found. Operating in SMART MOCK fallback mode.")

    def evaluate_relationship(
        self,
        adr: Dict[str, Any],
        artifact: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate if an ADR and another artifact (Issue/PR) are semantically
        linked to the same engineering decision.
        """
        prompt = self._build_prompt(adr, artifact)
        try:
            if self.gemini_key:
                return self._call_gemini(prompt)
            elif self.groq_key:
                return self._call_groq(prompt)
            elif self.openai_key:
                return self._call_openai(prompt)
        except Exception as e:
            print(f"LLM API call failed: {e}. Falling back to mock evaluation.")
        return self._smart_mock_evaluation(adr, artifact)

    def _build_prompt(self, adr: Dict[str, Any], art: Dict[str, Any]) -> str:
        return f"""You are a senior software architect analyzing the relationship between two engineering artifacts to reconstruct technical decisions.

Artifact A (Architecture Decision Record - ADR):
ID: {adr.get("external_id")}
Title: {adr.get("title")}
Content:
{adr.get("content")}

Artifact B ({art.get("source_type").upper()}):
ID: {art.get("external_id")}
Title: {art.get("title")}
Content:
{art.get("content")[:1000]}

Evaluate if Artifact B was created as a direct result of the decision made in Artifact A, or describes a problem/context that Artifact A specifically solves.

Provide your evaluation strictly as a JSON object matching this structure:
{{
  "related": true or false,
  "relationship_type": "implements_decision" (if B implements A) or "resolves_issue" (if A solves B) or "other",
  "confidence": float between 0.0 and 1.0,
  "reasoning": "A brief explanation of your reasoning (max 2 sentences)."
}}

Return ONLY the JSON. Do not include markdown codeblocks or conversational text.
"""

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._clean_and_parse_json(text)
        except Exception as e:
            print(f"Gemini API call failed: {e}.")
            raise e

    def _call_groq(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return self._clean_and_parse_json(text)
        except Exception as e:
            print(f"Groq API call failed: {e}.")
            raise e

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return self._clean_and_parse_json(text)
        except Exception as e:
            print(f"OpenAI API call failed: {e}.")
            raise e

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """
        Strips markdown codeblocks and parses raw JSON content.
        """
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Strip ```json ... ``` blocks
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except Exception as e:
            print(f"Failed to parse JSON response: {text}. Error: {e}")
            return {
                "related": False,
                "relationship_type": "other",
                "confidence": 0.0,
                "reasoning": "Failed to parse LLM response.",
            }

    def _smart_mock_evaluation(
        self,
        adr: Dict[str, Any],
        artifact: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        A smart, local keyword-matching evaluator. Returns highly probable
        matches for synthetic datasets without hitting external endpoints.
        """
        # Exclude already matched combinations
        adr_title = adr.get("title", "").lower()
        art_title = artifact.get("title", "").lower()
        art_content = artifact.get("content", "").lower()

        # Check for direct ID references (e.g. "ADR-0001" or "ADR-0012" mentioned in Issue body/title)
        adr_id = adr.get("external_id", "").lower()
        if adr_id and (adr_id in art_title or adr_id in art_content):
            return {
                "related": True,
                "relationship_type": "implements_decision",
                "confidence": 0.95,
                "reasoning": f"Mock LLM: Detected direct reference to {adr_id.upper()} in issue title or content.",
            }

        # Check for specific overlapping key terminology
        key_tech = [
            "redis",
            "sqs",
            "cache",
            "kubernetes",
            "postgres",
            "prometheus",
            "luxon",
            "kafka",
            "monitoring",
            "docker",
            "aws",
            "ledger",
            "security",
        ]
        
        adr_words = set(adr_title.split())
        art_words = set(art_title.split())
        common_words = adr_words.intersection(art_words)
        matched_tech = [w for w in common_words if w in key_tech]

        if matched_tech:
            return {
                "related": True,
                "relationship_type": "implements_decision",
                "confidence": 0.88,
                "reasoning": f"Mock LLM: Overlapping core technical concept(s) {matched_tech} found in titles.",
            }

        # Default fallback
        return {
            "related": False,
            "relationship_type": "other",
            "confidence": 0.0,
            "reasoning": "Mock LLM: No direct references or overlapping technical terms found in titles.",
        }

    def reconstruct_decision(
        self,
        adr: Dict[str, Any],
        cluster_text: str,
        connected_artifacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Reconstruct a structured decision from a seed ADR and its connected evidence.
        """
        if self.gemini_key or self.groq_key or self.openai_key:
            prompt = self._build_reconstruction_prompt(adr, cluster_text)
            try:
                if self.gemini_key:
                    return self._call_gemini(prompt)
                elif self.groq_key:
                    return self._call_groq(prompt)
                else:
                    return self._call_openai(prompt)
            except Exception as e:
                print(f"LLM API call failed: {e}. Falling back to mock reconstruction.")
        return self._smart_mock_reconstruction(adr, connected_artifacts)

    def _build_reconstruction_prompt(self, adr: Dict[str, Any], cluster_text: str) -> str:
        return f"""You are a senior software architect reconstructing an engineering decision by combining the architectural design record (ADR) with all downstream implementation evidence.

Seed ADR:
Title: {adr.get("title")}
Content:
{adr.get("content")}

Downstream Evidence (Commits, PRs, JIRA tickets):
{cluster_text[:4000]}

Reconstruct the decision and output it strictly as a JSON object matching this schema:
{{
  "title": "Short descriptive title of the decision",
  "problem": "The core problem addressed",
  "context": "Contextual background",
  "constraints": "Business or architectural constraints",
  "alternatives": "Alternative options considered",
  "decision": "Chosen technical solution",
  "reasoning": "Technical rationale",
  "implementation": "Summary of how it was implemented (including PR numbers, commit messages, repos)",
  "outcomes": "Operational outcomes, status, incidents, or deployments",
  "lessons": "Lessons learned or follow-ups"
}}

Return ONLY the JSON. Do not include markdown codeblocks or conversational text.
"""

    def _smart_mock_reconstruction(
        self,
        adr: Dict[str, Any],
        connected_artifacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Reconstruct decision using local metadata and text parsing.
        """
        meta = adr.get("metadata", {})
        content = adr.get("content", "")

        def extract_section(section_name: str) -> str:
            pattern = rf"##\s+{section_name}\s*(.*?)(?=\n##|$)"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        problem = extract_section("Problem") or adr.get("problem") or "Problem described in ADR."
        context = extract_section("Context") or adr.get("context") or "Context described in ADR."
        constraints = extract_section("Consequences") or adr.get("consequences") or "Operational consequences described in ADR."
        alternatives = extract_section("Alternatives") or adr.get("alternatives") or "Alternatives considered in ADR."
        decision = extract_section("Decision") or adr.get("decision") or "Decision described in ADR."
        
        reasoning = (
            extract_section("Reason")
            or extract_section("Reasoning")
            or adr.get("reason")
            or adr.get("reasoning")
            or "Rationale described in ADR."
        )

        # Summarize connected PRs and Commits
        prs = [a for a in connected_artifacts if a.get("source_type") == "pull_request"]
        commits = [a for a in connected_artifacts if a.get("source_type") == "commit"]
        tickets = [a for a in connected_artifacts if a.get("source_type") == "issue"]

        pr_list = ", ".join([f"PR #{p.get('external_id')}: \"{p.get('title')}\"" for p in prs])
        commit_list = f"{len(commits)} commits"
        ticket_list = ", ".join([f"Jira {t.get('external_id')}" for t in tickets])

        impl = (
            f"Implemented via {pr_list or 'PRs'}. "
            f"Linked commits: {commit_list}. "
            f"Work tracked under tickets: {ticket_list or 'none'}."
        )

        # Outcomes and incidents from metadata
        deployments = meta.get("linked_deployments", [])
        incidents = meta.get("linked_incidents", [])
        outcome_summary = meta.get("outcome_summary") or extract_section("Outcome") or "Deployed and operational."

        outcomes = (
            f"Outcome: {outcome_summary}. "
            f"Linked Deployments: {', '.join(deployments) if deployments else 'none'}. "
            f"Linked Incidents: {', '.join(incidents) if incidents else 'none'}."
        )
        
        lessons = (
            f"Operational consequences: {constraints}. "
            f"Expected benefits: {extract_section('Expected Benefits')}."
        )

        return {
            "title": adr.get("title", "Structured Decision"),
            "problem": problem,
            "context": context,
            "constraints": constraints,
            "alternatives": alternatives,
            "decision": decision,
            "reasoning": reasoning,
            "implementation": impl,
            "outcomes": outcomes,
            "lessons": lessons,
            "confidence": 0.95,
        }

    def generate_text(self, prompt: str) -> str:
        """
        Generate raw, non-JSON free-form text response from the active LLM provider.
        """
        if self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"Gemini generate_text failed: {e}")
                raise e

        elif self.groq_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.groq_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"Groq generate_text failed: {e}")
                raise e

        elif self.openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"OpenAI generate_text failed: {e}")
                raise e

        # Local conversational fallback (when no API keys are configured at all)
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]):
            return "Hello! I am your DecisionDNA AI assistant. How can I help you trace architectural decisions or explore engineering evidence today?"
        elif any(w in p_lower for w in ["who are you", "what is your name", "identify yourself"]):
            return "I am DecisionDNA AI, a decision intelligence agent trained to trace technical architectural decisions across your developer ecosystem."
        else:
            return (
                "Hello! I am your DecisionDNA AI assistant. I couldn't find any direct architectural decisions "
                "or evidence matching your query. Could you please specify a project name, database technology (e.g. Redis, SQS), "
                "or incident ID you'd like me to trace?"
            )

