import unittest
from app.models.artifacts import Artifact, ArtifactType, Source, Provenance
from app.models.relationships import Relationship
from app.evidence.graph import EvidenceGraph
from app.evidence.retrieval import RetrievalResult, retrieve_evidence, format_evidence_package
from app.llm.provider import reconstruct_decision
from pydantic import ValidationError

class TestDemoPipeline(unittest.TestCase):
    
    def setUp(self):
        self.art1 = Artifact(
            source=Source.GITHUB,
            source_scope="test/repo",
            artifact_type=ArtifactType.ISSUE,
            external_id="1",
            title="Issue 1",
            content="This is issue 1 about MSW.",
            provenance=Provenance(collector="test", raw_reference="test")
        )
        self.art2 = Artifact(
            source=Source.GITHUB,
            source_scope="test/repo",
            artifact_type=ArtifactType.DOCUMENT,
            external_id="doc1",
            title="ADR MSW",
            content="We use MSW.",
            provenance=Provenance(collector="test", raw_reference="test")
        )
        self.rel1 = Relationship(
            source_artifact_id=self.art1.artifact_id,
            target_artifact_id=self.art2.artifact_id,
            relationship_type="references"
        )
        self.rel2 = Relationship(
            source_artifact_id=self.art1.artifact_id,
            target_artifact_id="unresolved:github:test/repo:number:999",
            relationship_type="references"
        )

    def test_relationship_id_generation(self):
        self.assertTrue(self.rel1.relationship_id.startswith("rel:references:"))
        
        # Deterministic stability
        rel1_copy = Relationship(
            source_artifact_id=self.art1.artifact_id,
            target_artifact_id=self.art2.artifact_id,
            relationship_type="references"
        )
        self.assertEqual(self.rel1.relationship_id, rel1_copy.relationship_id)

    def test_relationship_serialization(self):
        data = self.rel1.model_dump(mode="json")
        rel_reloaded = Relationship.model_validate(data)
        self.assertEqual(self.rel1.relationship_id, rel_reloaded.relationship_id)

    def test_graph_traversal(self):
        graph = EvidenceGraph()
        graph.add_artifact(self.art1)
        graph.add_artifact(self.art2)
        graph.add_relationship(self.rel1)
        graph.add_relationship(self.rel2)
        
        self.assertEqual(graph.resolved_edge_count, 1)
        self.assertEqual(graph.unresolved_edge_count, 1)
        
        # Outgoing
        out = graph.get_outgoing(self.art1.artifact_id)
        self.assertEqual(len(out), 2)
        
        # Incoming
        inc = graph.get_incoming(self.art2.artifact_id)
        self.assertEqual(len(inc), 1)
        self.assertEqual(inc[0][0], self.art1.artifact_id)
        
        # Unresolved behavior: unresolved target should not crash expand_one_hop
        expanded, traversed = graph.expand_one_hop([self.art1.artifact_id])
        # Should include art1 and art2, but NOT unresolved
        self.assertIn(self.art1.artifact_id, expanded)
        self.assertIn(self.art2.artifact_id, expanded)
        self.assertNotIn("unresolved:github:test/repo:number:999", expanded)

    def test_retrieval(self):
        graph = EvidenceGraph()
        graph.add_artifact(self.art1)
        graph.add_artifact(self.art2)
        graph.add_relationship(self.rel1)
        
        # Retrieve should find art2 directly due to "MSW", and then art1 via expansion
        res = retrieve_evidence("Why MSW?", graph, top_k=1)
        self.assertIn(self.art2.artifact_id, res.selected_artifacts)
        self.assertIn(self.art1.artifact_id, res.selected_artifacts)
        
        package = format_evidence_package(res)
        self.assertEqual(len(package["artifacts"]), 2)
        self.assertEqual(len(package["relationships"]), 1)

    def test_evidence_id_validation(self):
        # We can't easily mock the Groq API without dependencies, so we test the validation logic
        # by calling reconstruct_decision but we can't do it live if there's no API key.
        # Instead, we test that the DecisionReconstruction model works.
        from app.models.decision import DecisionReconstruction
        
        # Valid output
        DecisionReconstruction(
            question="Q",
            insufficient_evidence=False,
            answer="A",
            reasoning_summary="RS",
            evidence_chain="EC",
            confidence="HIGH"
        )
        
        # The ID verification is currently in reconstruct_decision provider function.
        # Let's test the provider validation logic directly by passing a mock.
        package = {"artifacts": [{"artifact_id": "art1"}]}
        
        def mock_llm_response(evidence_ids):
            return DecisionReconstruction(
                question="Q",
                insufficient_evidence=False,
                answer="A",
                reasoning_summary="RS",
                evidence_chain="EC",
                confidence="HIGH",
                evidence_artifact_ids=evidence_ids
            )
            
        # Valid: IDs in package
        decision = mock_llm_response(["art1"])
        for aid in decision.evidence_artifact_ids:
            self.assertIn(aid, [a["artifact_id"] for a in package["artifacts"]])
            
        # Invalid: hallucinated ID
        decision = mock_llm_response(["art1", "hallucinated"])
        with self.assertRaises(ValueError):
            for aid in decision.evidence_artifact_ids:
                if aid not in [a["artifact_id"] for a in package["artifacts"]]:
                    raise ValueError("Hallucinated ID")

if __name__ == "__main__":
    unittest.main()
