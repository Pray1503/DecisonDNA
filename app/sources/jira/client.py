import json
from pathlib import Path
from typing import Dict, Any, List


class JiraClient:
    """
    Client for JIRA API. Simulates fetching tickets from the organization.
    """
    def __init__(self, data_path: Path | str | None = None):
        self.data_path = Path(data_path or "D:/dataset generator/OrgMemory-10K/jira/jira_tickets.json")

    def get_tickets(self) -> List[Dict[str, Any]]:
        """
        Fetch all JIRA tickets.
        """
        if not self.data_path.exists():
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)
