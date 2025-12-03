from __future__ import annotations

import time
from typing import Dict

import requests


class PortainerClient:
    def __init__(self, base_url: str, verify_tls: bool = True, api_key: str | None = None):
        self.base_url = f"{base_url}/api"
        self.verify_tls = verify_tls
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("API key authentication is required")
        return {"X-API-Key": self.api_key}

    def get_stack(self, stack_id: int) -> Dict:
        url = f"{self.base_url}/stacks/{stack_id}"
        response = requests.get(url, headers=self._headers(), verify=self.verify_tls, timeout=30)
        response.raise_for_status()
        return response.json()

    def start_stack(self, stack_id: int, *, endpoint_id: int) -> None:
        url = f"{self.base_url}/stacks/{stack_id}/start"
        params = {"endpointId": endpoint_id}
        response = requests.post(
            url,
            headers=self._headers(),
            params=params,
            verify=self.verify_tls,
            timeout=60,
        )
        response.raise_for_status()

    def stop_stack(self, stack_id: int, *, endpoint_id: int) -> None:
        url = f"{self.base_url}/stacks/{stack_id}/stop"
        params = {"endpointId": endpoint_id}
        response = requests.post(
            url,
            headers=self._headers(),
            params=params,
            verify=self.verify_tls,
            timeout=60,
        )
        response.raise_for_status()

    @staticmethod
    def stack_is_running(stack: Dict) -> bool:
        """Return True when the stack status reflects an active state."""

        status_value = stack.get("Status")
        if not isinstance(status_value, (int, float)):
            return False

        # Portainer documents status 1=active, 2=inactive
        return int(status_value) == 1

    def wait_until_running(self, stack_id: int, timeout_seconds: int = 300, interval_seconds: int = 5) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            stack = self.get_stack(stack_id)
            if self.stack_is_running(stack):
                return True
            time.sleep(interval_seconds)
        return False
