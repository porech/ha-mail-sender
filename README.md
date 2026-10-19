# HA Mail Sender

Saved emails for Home Assistant: choose a verified Gmail sender, write the message
once, and send it from a button, automation or Alexa routine. Each saved email
has its own persistent send limit.

**Early release:** automated tests exercise real Home Assistant flows and mocked
Gmail HTTP responses. Live Gmail delivery and Alexa activation still need testing
on a real installation. This is not an official Home Assistant or Google project.

**Documentation:** [English installation guide](docs/installation.md) ·
[Italian translation](docs/it/INSTALLAZIONE.md)

English is the project's primary language for documentation, code, issues and
release notes. The interface follows your Home Assistant profile language, with
English as the fallback. Available translations: English, German, Spanish, French,
Italian, Brazilian Portuguese and Simplified Chinese.
See [translation guidelines](docs/translations.md) to contribute another language.

## Why another integration?

Home Assistant's [Google Mail integration](https://www.home-assistant.io/integrations/google_mail/)
provides Google authentication. [Email Notifier](https://github.com/microteq/email_notifier)
provides SMTP notifications and account configuration. HA Mail Sender adds a
catalogue of saved messages, buttons, status and persistent limits, using the
existing Google Mail OAuth connection. It is an independent project, not a fork.

The Gmail API mailbox remains **`users/me`**. A verified custom send-as address
belongs in the message's **From header**, independently of the authenticated
Google account. Setup lists verified aliases and lets you select one; delivery
checks that it is still verified. No Google password, app password or token is
copied into this integration's configuration.

## Install

Requires **Home Assistant 2026.2.3 or newer**. Google Mail must already be added in
**Settings → Devices & services**, including Gmail API/OAuth setup as described in
its [official instructions](https://www.home-assistant.io/integrations/google_mail/).
Being signed into Gmail in a browser does not connect Home Assistant.

1. In HACS, open **⋮ → Custom repositories**.
2. Add `https://github.com/porech/ha-mail-sender`, category **Integration**.
3. Download **HA Mail Sender** (enable prereleases if needed for the initial beta)
   and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → HA Mail Sender**.
5. Name the saved email, choose the Google Mail account, select the sender alias,
   then enter To, optional Cc/Bcc, subject, message and limit.

Alternatively, copy `custom_components/ha_mail_sender` into
`<config>/custom_components/ha_mail_sender` and restart Home Assistant.

This repository is installable as a **HACS custom repository**; it is not included
in the default HACS catalogue.

## Configure and use

Add another integration entry for each saved email. Use **Configure → Edit saved
email** to change settings. Addresses are bare ASCII email addresses separated by
commas, without display names. The message is plain text, with multiline/Unicode
support. Templates containing Jinja are not evaluated.

Each saved email creates a device with:

- **Send** button: submits the saved email through the same delivery gate.
- **Status** sensor: ready, pending, accepted, failed or uncertain.

Add the entities to a dashboard or use `button.press` in an automation. See
[examples/dashboard.yaml](examples/dashboard.yaml). Entity IDs depend on the name
and language of your installation; select your actual entities in Home Assistant.

The status sensor includes `last_attempt`, `last_accepted`, `next_allowed`,
`last_result`, and a generic error category. A blocked press keeps the previous
submission status; `last_result` becomes `blocked`. Credentials, recipients and
message content are not exposed as state attributes. Home Assistant itself stores
saved message content in its configuration, so protect your configuration/backups.

### Alexa

Keep your existing Alexa/Home Assistant connection. Expose the **Send** button to
Alexa if your connection supports buttons as scenes, then create an Alexa routine:

> When you say “Alexa, send the request”, activate the corresponding scene.

If the button is not available, create a Home Assistant **script** containing
`button.press`, expose that script to Alexa, and select it in the routine's scene
action. [Example script](examples/script.yaml) and
[Home Assistant Alexa documentation](https://www.home-assistant.io/integrations/alexa.smart_home/).

The phrase is configured in the Alexa app. A routine's generic “OK” acknowledges
activation; it does not confirm Gmail acceptance. Check the status sensor, or use
its state in your own notification automation.

### Limits and delivery semantics

- **Once per calendar day** (default): one attempt per date in Home Assistant's
  configured timezone. The limit resets at local midnight, including DST changes.
- **Minimum interval**: wait the specified number of elapsed hours between attempts.
- **No limit**: successive requests can send again; overlapping requests are still
  dropped.

Repeated requests are discarded immediately, never queued. Each saved email has a
separate limit. Editing a message preserves its reservation timestamp and applies
the currently configured policy/interval to that timestamp. Renaming preserves
entity identity; deleting and recreating an entry creates a new limiter.

A reservation is saved **before** contacting Gmail and survives ordinary restarts
and integration reloads. Reload/unload waits for an active send before replacing
the runtime. A pending reservation found after restart is marked **uncertain**.
Unexpected power loss, restoring an older backup or deleting storage cannot offer
an exactly-once guarantee.

**Errors also consume the configured interval.** An HTTP timeout can happen after
Gmail accepted the message. There are no automatic retries. After checking Gmail's
Sent Mail, use **Configure → Reset a failed or uncertain attempt** to allow a manual
retry. Reset sends nothing and cannot clear an accepted submission's reservation.

“Accepted” means Gmail returned a message ID. It does not guarantee delivery to
an inbox, that an external alias's SMTP relay succeeded, or that the recipient read
it. Gmail applies your existing send-as routing/settings. Create and verify aliases
in Gmail itself; this integration does not create aliases or change signatures.

## Troubleshooting

- **No account:** add the official Google Mail integration first.
- **Cannot read aliases:** check Google Mail authentication, Gmail API availability,
  and its `gmail.settings.basic` permission; reconnect the account if necessary.
- **Sender absent:** finish verification in Gmail's **Send mail as** settings.
- **Failed/uncertain:** inspect Sent Mail before resetting the reservation; verify
  account authorization and external sender relay settings.
- **Daily timing:** check **Settings → System → General → Time zone**.
- **Google OAuth expires weekly:** follow the official Google Mail instructions for
  the OAuth app's publishing status.

Removing a saved email from Devices & services removes its limiter history. To
uninstall, remove all entries, uninstall in HACS (or delete the component directory)
and restart. Removing HA Mail Sender does not revoke the Google Mail connection.

## Development

```sh
uv venv --python 3.13 /tmp/ha-mail-sender-dev
uv pip install --python /tmp/ha-mail-sender-dev/bin/python -r requirements-test.txt
/tmp/ha-mail-sender-dev/bin/python -m pytest
/tmp/ha-mail-sender-dev/bin/ruff check .
/tmp/ha-mail-sender-dev/bin/ruff format --check .
```

The suite runs against Home Assistant 2026.2.3 / Python 3.13 and Home Assistant
2026.10.2 / Python 3.14. Tests use synthetic accounts and intercept HTTP. Never add real credentials,
recipient addresses or message content to issues, examples or test fixtures.

MIT licensed. Contributions and reproducible bug reports are welcome.
