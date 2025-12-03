# portainer-initiator

A lightweight helper that starts Portainer stacks sequentially on host startup. The container authenticates to Portainer, starts stacks one at a time, waits for each stack to report a running state, and optionally calls a webhook on success or failure.

## Configuration

Set the following environment variables (for example via an `.env` file used by Docker Compose):

- `PORTAINER_URL` (required): Base URL to Portainer, e.g. `https://portainer.example.com`.
- `PORTAINER_API_KEY` (required): API key generated in Portainer.
- `STACK_SEQUENCE` (required): Comma-separated list of stack IDs in the order they should start (e.g. `12,15,9`).
- `WEBHOOK_URL` (optional): URL to call with JSON payloads on success or failure events.
- `POLL_INTERVAL_SECONDS` (default `5`): Delay between status checks for a stack.
- `POLL_TIMEOUT_SECONDS` (default `300`): Maximum time to wait for a stack to report running before failing.
- `VERIFY_TLS` (default `true`): Set to `false` to skip TLS verification when connecting to Portainer.

## Running with Docker Compose

1. Create an `.env` file with your Portainer and stack details.
2. Start the helper container:

```sh
docker compose up -d
```

The container uses `restart: unless-stopped` so it will come up automatically after host reboots.

## Behavior

- If a stack is already running, it is stopped before being started again.
- Starts each stack sequentially, waiting for the current stack to be running before moving to the next. The helper uses each stack's `EndpointId` value when calling Portainer's `/stacks/{id}/start` API (Portainer CE 2.33.5) to align with the documented contract.
- Stops the sequence if a stack cannot be started or verified as running, and sends a failure webhook payload.
- Sends a webhook payload when the entire sequence completes successfully.
