import json
from pathlib import Path
from typing import Dict, Any, List


class KubernetesClient:
    """
    Client for Kubernetes deployment actions and CI/CD pipelines. Simulates fetching deployment events.
    """
    def __init__(self, data_path: Path | str | None = None):
        self.data_path = Path(data_path or Path(__file__).resolve().parents[3] / "OrgMemory-10K/deployments/deployments.json")

    def get_deployments(self) -> List[Dict[str, Any]]:
        """
        Fetch simulated deployments logs.
        """
        if not self.data_path.exists():
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)
