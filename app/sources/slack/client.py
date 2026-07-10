import json
from pathlib import Path
from typing import Dict, Any, List


class SlackClient:
    """
    Client for Slack. Simulates fetching channel messages and retro chats from developer feedback.
    """
    def __init__(self, data_path: Path | str | None = None):
        self.data_path = Path(data_path or "D:/dataset generator/OrgMemory-10K/feedback/developer_feedback.json")

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Fetch simulated Slack/retro messages.
        """
        if not self.data_path.exists():
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)
