from typing import Dict, Any
from app.models.artifact import Artifact


class KubernetesNormalizer:
    """
    Normalizes Kubernetes deployment events into Universal Artifacts.
    """
    def __init__(self, default_context: dict | None = None):
        self.default_context = default_context or {}

    def normalize_deployment(self, raw_dep: Dict[str, Any]) -> Artifact:
        dep_id = str(raw_dep.get("deployment_id") or "")
        if not dep_id:
            raise ValueError("Deployment must have a deployment_id")

        pipeline_run = raw_dep.get("pipeline_run") or ""
        # Extract repository from pipeline_run url if available
        # e.g., "https://github.com/novatech-solutions/atlaspay-backend/actions/runs/38818"
        repo = None
        if "github.com/" in pipeline_run:
            parts = pipeline_run.split("github.com/")[1].split("/")
            if len(parts) >= 2:
                repo = parts[1]

        environment = raw_dep.get("environment") or "production"
        title = f"Deploy {dep_id} to {environment}"
        content = f"Pipeline Run: {pipeline_run}\nStatus: {raw_dep.get('status')}\nRollback: {raw_dep.get('rollback')}"
        author = "k8s-runner"

        timestamps = {}
        if raw_dep.get("timestamp"):
            timestamps["created_at"] = raw_dep["timestamp"]
            timestamps["deployed_at"] = raw_dep["timestamp"]

        context = {**self.default_context}
        if repo:
            context["repository"] = repo

        metadata = {
            "environment": environment,
            "pipeline_run": pipeline_run,
            "duration_seconds": raw_dep.get("duration_seconds"),
            "status": raw_dep.get("status"),
            "rollback": raw_dep.get("rollback"),
            "linked_pr": raw_dep.get("linked_pr"),
            "linked_adr": raw_dep.get("linked_adr"),
        }

        artifact_id = Artifact.generate_id(
            source="kubernetes",
            source_type="deployment",
            external_id=dep_id,
            context=context,
        )

        provenance = {
            "connector": "KubernetesConnector",
            "version": "1.0.0",
        }

        return Artifact(
            artifact_id=artifact_id,
            source="kubernetes",
            source_type="deployment",
            external_id=dep_id,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            context=context,
            metadata=metadata,
            provenance=provenance,
        )
