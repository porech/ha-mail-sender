# Installation and setup

HA Mail Sender stores prewritten emails and sends them through Gmail. Each saved
email has its own send limit and a button you can connect to an Alexa routine.

Requires **Home Assistant 2026.2.3 or newer**.

## Connect Gmail to Home Assistant

Look for **Google Mail** in **Settings → Devices & services**. If it is missing,
add it using the [official setup instructions](https://www.home-assistant.io/integrations/google_mail/).
You will need a Google Cloud project with the Gmail API enabled, OAuth credentials,
and authorization from your Google account. Being signed into Gmail in a browser
does not connect it to Home Assistant.

HA Mail Sender reuses that connection. You do not need to enter a Gmail password,
an app password or separate SMTP credentials in this integration.

To use a custom sender address, first add and verify it in Gmail under
**Settings → See all settings → Accounts and Import → Send mail as**. Your
authenticated Google account and the message's sender address are separate.

## Install HA Mail Sender

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/porech/ha-mail-sender`, category **Integration**.
3. Download **HA Mail Sender**. Enable prereleases if needed to select the beta.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration → HA Mail Sender**.

For manual installation, copy `custom_components/ha_mail_sender` from the repository
to `<config>/custom_components/ha_mail_sender` and restart Home Assistant.

## Create a saved email

1. Enter a name and select an existing Google Mail account.
2. Select a verified sender address from the list.
3. Enter the recipients, optional Cc/Bcc addresses, subject and message.
4. Choose the send limit and save.

Setup does not send any email. Add another integration entry for each saved
message. To change an existing one, use **Configure → Edit saved email**.

Enter bare email addresses separated by commas, without display names. The message
is plain text and supports multiple lines and Unicode. Jinja expressions are not
evaluated.

Each entry creates a **Send** button and a **Status** sensor. Add them to a
dashboard, or call `button.press` from an automation. The interface uses your Home
Assistant profile language; English is the fallback for unsupported languages.

## Connect Alexa

Use your existing Alexa connection to expose the **Send** button to Alexa as a
scene, if supported. In the Alexa app, create a routine that activates that scene
when you say your chosen phrase.

If the button is not available, create a Home Assistant **script** that calls
`button.press`, expose that script to Alexa, and select it as the routine's scene
action. Use the [example script](../examples/script.yaml), replacing its entity ID
with the actual Send button on your installation.

Configure the spoken phrase in Alexa and the message settings in Home Assistant.
Alexa's generic acknowledgment confirms activation, not email submission; check
the Status sensor for the result.

## Choose a send limit

- **Once per calendar day:** one attempt per date in Home Assistant's timezone.
- **Minimum interval:** wait the configured number of elapsed hours.
- **No limit:** allow successive attempts; overlapping requests are still blocked.

Repeated requests are discarded rather than queued. Each saved email has a
separate limit. The reservation is saved before submission and retained across
ordinary restarts and integration reloads. Editing a message preserves its
reservation timestamp and applies the currently selected policy to that timestamp.

Errors also consume the configured interval, because a timeout can occur after
Gmail accepted the email. There are no automatic retries. Check Gmail's **Sent
Mail** first. If another attempt is needed, use **Configure → Reset a failed or
uncertain attempt**. Resetting permits another attempt but sends nothing. This
option cannot clear an accepted submission's reservation.

**Accepted by Gmail** means the API returned a message ID. It does not confirm
inbox delivery or successful delivery through an external alias's relay. Gmail
uses the existing routing settings for your verified sender.

## Verification and troubleshooting

This beta has automated tests against real Home Assistant APIs and simulated Gmail
HTTP responses. Live Gmail delivery with your account and Alexa activation still
need to be verified on your installation.

For authentication errors, missing senders, timezone settings and removal
instructions, see [Troubleshooting in the README](../README.md#troubleshooting).

Documentation translation: [Italian](it/INSTALLAZIONE.md).
