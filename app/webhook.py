from __future__ import annotations

import json
from typing import Any, Dict

import requests


def send_webhook(url: str, event: str, payload: Dict[str, Any]) -> None:
    body = {"event": event, "payload": payload}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
    response.raise_for_status()
