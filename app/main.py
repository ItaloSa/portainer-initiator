from __future__ import annotations

import logging
import sys
import threading
from typing import List

from app.config import Settings
from app.portainer import PortainerClient
from app.webhook import send_webhook

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class StackStarter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = PortainerClient(
            base_url=settings.portainer_url,
            verify_tls=settings.verify_tls,
            api_key=settings.portainer_api_key or None,
        )

    def notify(self, event: str, payload: dict) -> None:
        if not self.settings.webhook_url:
            return
        try:
            send_webhook(self.settings.webhook_url, event, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send webhook for %s: %s", event, exc)

    def ensure_stack_running(self, stack_id: int) -> bool:
        stack = self.client.get_stack(stack_id)
        endpoint_id = stack.get("EndpointId")
        if endpoint_id is None:
            logger.error("Stack %s is missing EndpointId; cannot start", stack_id)
            return False

        if self.client.stack_is_running(stack):
            logger.info("Stack %s already running; stopping before restart", stack_id)
            self.client.stop_stack(stack_id, endpoint_id=endpoint_id)

        logger.info("Starting stack %s", stack_id)
        self.notify("stack_starting", {"stack_id": stack_id})
        self.client.start_stack(stack_id, endpoint_id=endpoint_id)
        running = self.client.wait_until_running(
            stack_id,
            timeout_seconds=self.settings.poll_timeout_seconds,
            interval_seconds=self.settings.poll_interval_seconds,
        )
        if running:
            logger.info("Stack %s is running", stack_id)
        else:
            logger.error("Timed out waiting for stack %s to become healthy", stack_id)
        return running

    def run(self) -> bool:
        for stack_id in self.settings.stack_sequence:
            logger.info("Processing stack %s", stack_id)
            if not self.ensure_stack_running(stack_id):
                self.notify(
                    "stack_failed",
                    {"stack_id": stack_id, "message": "Failed to start or verify stack"},
                )
                return False

        self.notify("stack_sequence_complete", {"stacks": self.settings.stack_sequence})
        logger.info("All stacks started successfully")
        return True


def _wait_for_manual_stop() -> None:
    logger.info("Waiting for manual shutdown (Ctrl+C or docker stop)...")
    stop_event = threading.Event()
    try:
        while not stop_event.wait(timeout=60):
            continue
    except KeyboardInterrupt:
        logger.info("Shutdown requested; exiting")


def main(argv: List[str] | None = None) -> int:
    try:
        settings = Settings.load()
    except Exception as exc:  # noqa: BLE001
        logger.error("Configuration error: %s", exc)
        _wait_for_manual_stop()
        return 0

    starter = StackStarter(settings)
    try:
        succeeded = starter.run()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error while starting stacks: %s", exc)
        succeeded = False

    if succeeded:
        logger.info("Stack startup sequence completed; keeping container running for manual stop")
    else:
        logger.error("Stack startup sequence failed; keeping container running for manual stop")

    _wait_for_manual_stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
