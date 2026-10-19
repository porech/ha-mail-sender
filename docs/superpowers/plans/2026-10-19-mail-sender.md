# HA Mail Sender Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans, task by task.

**Goal:** Publish a usable Home Assistant integration for saved, rate-limited emails.
**Architecture:** One config entry per saved email; native config/options flows,
button and status sensor; independent delivery controller with persisted state.
**Tech Stack:** Python standard-library email, Gmail API via HA OAuth helpers, Home Assistant, pytest, Ruff.
**Spec:** `docs/superpowers/specs/2026-10-19-mail-sender-design.md`

## Global Constraints
No real emails or personal data in development/publication. Reuse Google Mail OAuth. TLS verification on.
No automatic retry or queuing. Calendar-day limits use the HA timezone. Native UI.
Temporary development venv only; do not install in global or project environments.

## Review Focus
- Gmail acceptance and HTTP disconnects must not trigger automatic duplicates.
- Restart during a send must preserve a conservative reservation.
- Reload/removal during delivery must not release the gate prematurely.
- Local midnight and DST must follow calendar dates, not a fixed 24-hour delay.
- Native options changes must preserve entity identity and limiter history.

### Task 1: Delivery core
Files: `custom_components/ha_mail_sender/{models,delivery}.py`, `tests/test_delivery.py`.
Interfaces: `MailConfig.from_mapping(data)`, `build_message(config)`,
`GmailTransport.async_send(config)`, `DeliveryController(config, state, save, send, now, changed)`;
`async_send() -> str`, `next_allowed() -> datetime | None`.
- [x] Write failing tests for recipients, validation, daily/interval limits,
  concurrency, persisted pending state, save failure and Gmail API errors.
- [x] Run tests and observe failures, implement core, rerun until green.
- [x] Commit tested core.

### Task 2: Native integration
Files: `__init__.py`, `config_flow.py`, `button.py`, `sensor.py`, `const.py`,
`manifest.json`, `strings.json`, `translations/{en,it}.json`, `tests/test_integration.py`.
Consumes Task 1 interfaces; produces add/edit/send/status/reset native HA flows.
- [x] Write failing integration tests against Home Assistant, mocking Gmail HTTP responses.
- [x] Implement forms, runtime setup/unload, storage and entities.
- [x] Verify options reload, state restoration, send button and reset policy.
- [x] Commit tested integration.

### Task 3: Distribution
Files: README, Italian guide, license, HACS metadata, CI and example dashboard.
- [x] Explain installation, Google Mail OAuth prerequisites, Alexa routine, limits and errors.
- [x] Run full pytest and Ruff checks; review source and fix important issues.
- [x] Create/push public repo, inspect CI, tag prerelease after checks pass.

## Rulings and progress

The user clarified Gmail with an existing verified custom sender. SMTP code was
replaced with Gmail API transport reusing public Home Assistant OAuth helpers;
account identity stays `me` while the MIME From contains the verified alias.
The design reviewer highlighted reload safety, durable pending reservations and
separate acceptance timestamps; these are implemented and tested. Python compares
repeated local DST hours by wall time, so limiter comparisons use timestamps.
Verification: 36 tests pass on Home Assistant 2026.2.3 / Python 3.13 and
2026.10.2 / Python 3.14. Final independent review found HA Store suppresses write
failures; replaced it with an acknowledged atomic, file/directory-fsynced store.
Regression tests reproduce and prevent submission on failed storage replacement.
The reviewer verified the fix and reported no remaining important issues.
Published https://github.com/porech/ha-mail-sender and tagged v0.1.0-beta.1.
GitHub Actions runs 39262059507 and 39262123942 passed both test environments,
Ruff and hassfest. No live Home Assistant configuration or mail delivery was changed.
