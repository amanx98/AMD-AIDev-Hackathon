import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AMDModel:
    def __init__(self):
        self.base_url = os.getenv("AMD_BASE_URL", "")
        self.api_key = os.getenv("AMD_API_KEY", "")
        self.model = os.getenv("AMD_MODEL", "gemma-3-27b-it")
        self._client = None
        if self.base_url and self.api_key and OpenAI is not None:
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def reason(self, prompt: str):
        if not self.enabled:
            return None
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are LedgerLens, an accounts-payable reconciliation assistant. "
                            "Answer only from the provided policy and evidence. Be concise and cite the policy clause."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            return f"[model error: {exc}]"

    def status(self) -> str:
        return f"connected ({self.model})" if self.enabled else "offline (heuristic fallback)"
