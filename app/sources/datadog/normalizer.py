from typing import Dict, Any
from app.models.artifact import Artifact


class DatadogNormalizer:
    """
    Normalizes Datadog incident/outage records into Universal Artifacts.
    """
    def __init__(self, default_context: dict | None = None):
        self.default_context = default_context or {}

    def normalize_incident(self, raw_inc: Dict[str, Any]) -> Artifact:
        inc_id = str(raw_inc.get("incident_id") or "")
        if not inc_id:
            raise ValueError("Incident must have an incident_id")

        title = raw_inc.get("cause") or f"Incident Outage {inc_id}"
        content = raw_inc.get("root_cause") or ""
        author = "OnCall-Ops"
        project_name = raw_inc.get("_project_name")

        timestamps = {}
        if raw_inc.get("_detect_time"):
            timestamps["created_at"] = raw_inc["_detect_time"]
            timestamps["detected_at"] = raw_inc["_detect_time"]
        if raw_inc.get("_resolve_time"):
            timestamps["resolved_at"] = raw_inc["_resolve_time"]

        context = {**self.default_context}
        if project_name:
            context["project"] = project_name

        metadata = {
            "severity": raw_inc.get("severity"),
            "resolution": raw_inc.get("resolution"),
            "lessons_learned": raw_inc.get("lessons_learned"),
            "linked_deployment": raw_inc.get("linked_deployment"),
            "linked_pr": raw_inc.get("linked_pr"),
            "linked_adr": raw_inc.get("linked_adr"),
            "timeline": raw_inc.get("timeline") or [],
        }

        artifact_id = Artifact.generate_id(
            source="datadog",
            source_type="incident",
            external_id=inc_id,
            context=context,
        )

        provenance = {
            "connector": "DatadogConnector",
            "version": "1.0.0",
        }

        return Artifact(
            artifact_id=artifact_id,
            source="datadog",
            source_type="incident",
            external_id=inc_id,
            title=title,
            content=content,
            author=author,
            timestamps=timestamps,
            context=context,
            metadata=metadata,
            provenance=provenance,
        )
