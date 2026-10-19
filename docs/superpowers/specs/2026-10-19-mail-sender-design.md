# HA Mail Sender

## Intent and scope

Public `porech/ha-mail-sender`, a HACS custom integration for named, saved emails
sent from a Home Assistant button, automation or Alexa routine. Native config
and options forms cover sender, To/Cc/Bcc, subject, multiline text and per-email
limits. No personal data or credentials are published. English and Italian UI/docs.

The user clarified Gmail and an already verified custom Send mail as address.
Use the official Google Mail integration's existing OAuth connection through
Home Assistant's public OAuth helpers. No fork of the SMTP Email Notifier project,
no SMTP credentials and no new Google OAuth implementation. The authenticated
mailbox is always `users/me`; the selected verified alias goes into MIME From.
Read aliases through `settings/sendAs`, validate again at submission, send through
`messages/send`, and require a returned message ID. The user must configure Google
Mail first if absent. No live mail is sent during development or setup.

## Native UI and lifecycle

One config entry per saved email references a Google Mail entry ID and contains
its own fields and limit settings. No copied OAuth secrets. Config form chooses
account then verified alias and message fields; options edit or reset a failed or
uncertain reservation. Expose a Send button and Status enum sensor, with attempt,
acceptance, next allowed timestamps and last request result. Never expose content,
recipients or credentials as entity state. Renaming/editing preserves IDs/history.

Alexa phrases are configured in the Alexa app through the existing connection.
If direct button exposure is unavailable, document a Home Assistant script wrapping
`button.press` and expose that script as a scene. No promised voice confirmation.

## Limits and delivery

Daily policy uses Home Assistant's local calendar date; interval policy uses elapsed
UTC time, including repeated DST hours; none disables successive-request limits.
Concurrent requests are dropped. No queuing or retries. Save a pending reservation
before contacting Gmail. Persisted pending becomes uncertain after restart and
retains the limit. Any send failure conservatively retains the limit. Explicit
manual reset is restricted to failed/uncertain states after a mailbox check; reset
never sends mail. Accepted means API acceptance, not inbox delivery.

An active task is shielded from caller cancellation. Unload/reload closes the gate
and waits for it before replacement; deleting an entry removes its history. Failed
reservation save prevents sending; failed final save leaves durable pending history.
Policy edits retain the timestamp and apply the new policy. Backups/power failure
cannot offer an exactly-once guarantee.

## Build and verification

Python 3.13+, Home Assistant 2026.2.3+; no added runtime dependencies. Temporary
venvs only. Test native Home Assistant config/options/entity lifecycle and mocked
Gmail HTTP boundaries, alias validation, From/mailbox distinction, errors, Unicode,
concurrency, restart, storage failures and DST. English README, Italian quickstart,
MIT license, generic examples and CI. Publish an early prerelease, explicitly
stating that live Gmail and Alexa remain untested until configured on the user's HA.
