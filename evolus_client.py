import os

import requests


class EvolusClient:
    def __init__(self):
        self.base_url = os.getenv("EVOLUS_BASE_URL", "https://api.evolus.ai/api/v1")
        self.api_key = os.getenv("EVOLUS_API_KEY", "")
        self.application_id = os.getenv("EVOLUS_APPLICATION_ID", "")
        self.extractor_id = os.getenv("EVOLUS_EXTRACTOR_ID", "")
        self.workflow_id = os.getenv("EVOLUS_WORKFLOW_ID", "")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.application_id)

    @property
    def headers(self):
        return {"X-ApiKey": self.api_key, "X-Application-Id": self.application_id}

    def extract_document(self, filename: str, content: bytes):
        if not self.enabled or not self.extractor_id:
            return None
        url = f"{self.base_url}/extractors/{self.extractor_id}/run"
        response = requests.post(
            url, headers=self.headers, files={"file": (filename, content)}, timeout=120
        )
        response.raise_for_status()
        return response.json()

    def run_ai_tool(self, tool: str, payload: dict):
        if not self.enabled:
            return None
        url = f"{self.base_url}/ai-tools/{tool}/run"
        response = requests.post(url, headers=self.headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def execute_workflow(self, payload: dict):
        if not self.enabled or not self.workflow_id:
            return None
        url = f"{self.base_url}/workflows/{self.workflow_id}/execute"
        response = requests.post(url, headers=self.headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def status(self) -> str:
        return "connected" if self.enabled else "offline (mock connector)"
