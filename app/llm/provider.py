import os
import json
from pydantic import ValidationError
from typing import Optional

from app.models.decision import DecisionReconstruction

def reconstruct_decision(
    question: str, 
    evidence_package: dict, 
    model: str = "llama-3.3-70b-versatile"
) -> DecisionReconstruction:
    """
    Call Groq to reconstruct a decision based ONLY on the evidence package.
    """
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("The 'groq' package is required but not installed.")
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")
        
    client = Groq(api_key=api_key)
    model = os.environ.get("GROQ_MODEL", model)
    
    system_prompt = f"""You are an expert engineering assistant for DecisionDNA.
Your task is to answer the user's question by reconstructing a decision using ONLY the provided evidence package.

STRICT INSTRUCTIONS:
1. USE ONLY THE SUPPLIED EVIDENCE. Do NOT use outside knowledge.
2. Do not invent unsupported facts.
3. Distinguish direct evidence from inference.
4. CITE SUPPORTING ARTIFACT IDs for factual claims (use the exact `artifact_id`).
5. Do NOT cite Artifact IDs that were not supplied in the evidence package.
6. If the evidence is insufficient to answer the question, set `insufficient_evidence` to true and explain what is missing.
7. Only list `alternatives` or `outcome` if they are explicitly mentioned in the evidence.
8. Output your response in valid JSON matching the following schema perfectly. ALL REQUIRED FIELDS MUST BE PRESENT:

{json.dumps(DecisionReconstruction.model_json_schema(), indent=2)}"""

    evidence_str = json.dumps(evidence_package, indent=2, ensure_ascii=False)
    
    user_prompt = f"""EVIDENCE PACKAGE:
{evidence_str}

QUESTION:
{question}"""

    # We use JSON mode if supported, or just prompt engineering
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from Groq.")
        
    # Validate through Pydantic
    try:
        data = json.loads(content)
        decision = DecisionReconstruction.model_validate(data)
        
        # Verify that all evidence IDs are real and were supplied
        supplied_ids = {a["artifact_id"] for a in evidence_package.get("artifacts", [])}
        for aid in decision.evidence_artifact_ids:
            if aid not in supplied_ids:
                raise ValueError(f"LLM cited an unsupported or hallucinated artifact_id: {aid}")
                
        return decision
        
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse JSON from Groq: {content}")
