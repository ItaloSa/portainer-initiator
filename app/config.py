from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


def _bool_from_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_from_env(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _parse_stack_sequence(value: str | None) -> List[int]:
    if not value:
        return []
    ids: List[int] = []
    for raw in value.split(","):
        raw_id = raw.strip()
        if not raw_id:
            continue
        try:
            ids.append(int(raw_id))
        except ValueError:
            raise ValueError(f"Invalid stack id '{raw_id}'. STACK_SEQUENCE must be a comma-separated list of integers.") from None
    return ids


@dataclass
class Settings:
    portainer_url: str = field(default_factory=lambda: os.getenv("PORTAINER_URL", ""))
    portainer_api_key: str = field(default_factory=lambda: os.getenv("PORTAINER_API_KEY", ""))
    stack_sequence: List[int] = field(default_factory=list)
    webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("WEBHOOK_URL"))
    poll_interval_seconds: int = 5
    poll_timeout_seconds: int = 300
    verify_tls: bool = True

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        settings.portainer_url = os.getenv("PORTAINER_URL", "").rstrip("/")
        settings.portainer_api_key = os.getenv("PORTAINER_API_KEY", "")
        settings.stack_sequence = _parse_stack_sequence(os.getenv("STACK_SEQUENCE"))
        settings.webhook_url = os.getenv("WEBHOOK_URL")
        settings.poll_interval_seconds = _int_from_env(os.getenv("POLL_INTERVAL_SECONDS"), 5)
        settings.poll_timeout_seconds = _int_from_env(os.getenv("POLL_TIMEOUT_SECONDS"), 300)
        settings.verify_tls = _bool_from_env(os.getenv("VERIFY_TLS"), True)

        if not settings.portainer_url:
            raise ValueError("PORTAINER_URL is required")
        if not settings.portainer_api_key:
            raise ValueError("PORTAINER_API_KEY is required for authentication")
        if not settings.stack_sequence:
            raise ValueError("STACK_SEQUENCE must list at least one stack id (comma-separated integers)")

        return settings
