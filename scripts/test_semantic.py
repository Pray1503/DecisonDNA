import os
import sys
from pathlib import Path

# Ensure app is in the import path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.embeddings import EmbeddingService
from app.core.llm import LLMProvider


def test_embeddings():
    print("\n--- Testing EmbeddingService (Similarity) ---")
    
    # We set FORCE_TFIDF=1 to ensure the tests run instantly and locally in this test setup
    os.environ["FORCE_TFIDF"] = "1"
    
    service = EmbeddingService()
    assert service.use_fallback is True, "FORCE_TFIDF must activate local fallback"

    # Test related terms
    related_a = ["Implement Redis cache layer for security-scanner"]
    related_b = ["Spike: Evaluate options for Implement Redis cache layer for security-scanner"]
    
    similarity_matrix_related = service.calculate_similarities(related_a, related_b)
    score_related = float(similarity_matrix_related[0, 0])
    print(f"Similarity for related texts (ADR title vs JIRA Spike title): {score_related:.3f}")
    assert score_related >= 0.5, "Related texts must have a high similarity score"

    # Test unrelated terms
    unrelated_a = ["Implement Redis cache layer for security-scanner"]
    unrelated_b = ["Standardize container deployment pipeline using Kubernetes on AWS"]

    similarity_matrix_unrelated = service.calculate_similarities(unrelated_a, unrelated_b)
    score_unrelated = float(similarity_matrix_unrelated[0, 0])
    print(f"Similarity for unrelated texts (Redis vs Kubernetes): {score_unrelated:.3f}")
    assert score_unrelated < 0.1, "Unrelated texts must have low similarity score"
    assert score_unrelated < score_related, "Unrelated texts must have lower similarity than related texts"

    print("SUCCESS: EmbeddingService similarity checked.")


def test_llm_provider():
    print("\n--- Testing LLMProvider (Relationship Evaluation) ---")
    provider = LLMProvider()

    # Case 1: Linked via concept keyword
    mock_adr_1 = {
        "external_id": "ADR-0002",
        "title": "Implement Redis cache layer for security-scanner",
        "content": "Deploy Redis caching to reduce database read load."
    }
    mock_issue_1 = {
        "external_id": "SS23-1",
        "source_type": "issue",
        "title": "Spike: Options for Redis caching layer",
        "content": "We need a distributed cache cluster."
    }

    result_1 = provider.evaluate_relationship(mock_adr_1, mock_issue_1)
    print(f"Evaluation 1 (Related concepts):")
    print(f"  - Related: {result_1.get('related')}")
    print(f"  - Confidence: {result_1.get('confidence')}")
    print(f"  - Reasoning: {result_1.get('reasoning')}")
    assert result_1.get("related") is True, "Concept overlapping artifacts must evaluate to related"

    # Case 2: Unrelated concepts
    mock_adr_2 = {
        "external_id": "ADR-0001",
        "title": "Introduce AWS SQS for decoupled communications in atlaspay-ledger",
        "content": "Use AWS SQS."
    }
    mock_issue_2 = {
        "external_id": "SS23-1",
        "source_type": "issue",
        "title": "Standardize frontend components",
        "content": "Clean up React CSS styles."
    }

    result_2 = provider.evaluate_relationship(mock_adr_2, mock_issue_2)
    print(f"Evaluation 2 (Unrelated concepts):")
    print(f"  - Related: {result_2.get('related')}")
    print(f"  - Reasoning: {result_2.get('reasoning')}")
    assert result_2.get("related") is False, "Unrelated artifacts must evaluate to unrelated"

    print("SUCCESS: LLMProvider relationship evaluation checked.")


if __name__ == "__main__":
    test_embeddings()
    test_llm_provider()
    print("\nALL SEMANTIC TESTS PASSED SUCCESSFULLY!")
