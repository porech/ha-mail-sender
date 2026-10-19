# HA Mail Sender Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans, task by task.

**Goal:** Publish a usable Home Assistant integration for saved, rate-limited emails.
**Architecture:** One config entry per saved email; native config/options flows,
button and status sensor; independent delivery controller with persisted state.
**Tech Stack:** Python standard-library SMTP/email, Home Assistant, pytest, Ruff.
**Spec:** `docs/superpowers/specs/2026-10-19-mail-sender-design.md`

## Global Constraints
No real emails or personal data in development/publication. TLS verification on.
No automatic retry or queuing. Calendar-day limits use the HA timezone. Native UI.
Temporary development venv only; do not install in global or project environments.

## Review Focus
- Partial SMTP acceptance and disconnects must not trigger automatic duplicates.
- Restart during a send must preserve a conservative reservation.
- Reload/removal during delivery must not release the gate prematurely.
- Local midnight and DST must follow calendar dates, not a fixed 24-hour delay.
- Native options changes must preserve entity identity and limiter history.

### Task 1: Delivery core
Files: `custom_components/ha_mail_sender/{models,delivery}.py`, `tests/test_delivery.py`.
Interfaces: `MailConfig.from_mapping(data)`, `build_message(config)`,
`send_smtp(config)`, `DeliveryController(config, state, save, send, now, changed)`;
`async_send() -> str`, `next_allowed() -> datetime | None`.
- [ ] Write failing tests for recipients, validation, daily/interval limits,
  concurrency, persisted pending state, save failure and partial delivery.
- [ ] Run tests and observe failures, implement core, rerun until green.
- [ ] Commit tested core.

### Task 2: Native integration
Files: `__init__.py`, `config_flow.py`, `button.py`, `sensor.py`, `const.py`,
`manifest.json`, `strings.json`, `translations/{en,it}.json`, `tests/test_integration.py`.
Consumes Task 1 interfaces; produces add/edit/send/status/reset native HA flows.
- [ ] Write failing integration tests against Home Assistant, mocking only SMTP.
- [ ] Implement forms, runtime setup/unload, storage and entities.
- [ ] Verify options reload, state restoration, send button and reset policy.
- [ ] Commit tested integration.

### Task 3: Distribution
Files: README, Italian guide, license, HACS metadata, CI and example dashboard.
- [ ] Explain installation, SMTP authentication, Alexa routine, limits and errors.
- [ ] Run full pytest and Ruff checks; review source and fix important issues.
- [ ] Create/push public repo, inspect CI, tag prerelease after checks pass.
