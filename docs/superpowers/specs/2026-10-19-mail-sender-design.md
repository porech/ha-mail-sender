# HA Mail Sender

## Intent
Send prewritten emails from a Home Assistant button, automation or Alexa routine.
Users configure each message in Home Assistant, with real To/Cc/Bcc fields and a
persistent per-message rate limit. No personal addresses, medical details or
credentials belong in this public repository.

## First release
Native custom integration `ha_mail_sender`, installable as a HACS custom repository.
Each config entry represents one named saved email, with its own SMTP settings,
subject, multiline plain-text body, recipients, and rate-limit policy. Users can
add entries and edit their settings through native config/options forms. This
deliberately avoids a custom frontend and a separate server. Reusing SMTP settings
across messages is a possible future enhancement.

Each entry exposes a send button and status sensor. Button presses, including
Alexa scene activation, go through the same gate. Status includes last accepted
send, next permitted time and a safe error category, never recipients/body/password.
Alexa phrases are configured in the Alexa app; this integration does not configure
Alexa routines or promise spoken delivery confirmation.

## Delivery and limits
Policies: once per local calendar day (Home Assistant timezone), a configurable
rolling interval in hours, or no limit. Default: calendar day. Repeated requests
are dropped immediately, never queued. A per-entry lock serializes delivery;
concurrent requests are dropped even with limits disabled. State is stored before
SMTP submission to survive a restart during delivery. A persisted pending attempt
is treated as uncertain after restart and retains its limit. Explicit transport
errors retain a conservative limit too, since server acceptance may be ambiguous.
No automatic retries, and no public bypass button. Status distinguishes accepted,
blocked, failed/uncertain. A user can deliberately reset a failed/uncertain attempt
through the integration's options menu after checking their mailbox.

SMTP runs off the event loop. Support STARTTLS and implicit TLS with certificate
verification, and optional unauthenticated local relay. Validate headers, addresses,
port, interval and required text. A message has a single To/Cc/Bcc envelope;
Bcc must not appear in headers. Partial recipient refusal is an error, with no
automatic resend to successful recipients. SMTP acceptance is not inbox delivery.

## Publication and verification
Public GitHub repository `porech/ha-mail-sender`, MIT license, English and Italian
UI strings, English README and Italian quickstart, generic examples, CI and a
tagged initial prerelease. Require Home Assistant 2026.1+ / Python 3.13+ (verify
against the locally installable Home Assistant test environment). No live mail
is sent while developing. Tests must cover MIME/envelope recipients, invalid
configuration, limits at local midnight/DST, concurrency, restart state, errors,
and native config/options/entity lifecycle against real Home Assistant APIs.

## Decisions made by the builder
One saved email per config entry keeps adding/editing/removing messages native.
Conservative handling of uncertain delivery trades an occasional manual check for
avoiding repeated mail. Credential checks during setup connect/login only, never
send a test message. Public examples describe generic requests.
