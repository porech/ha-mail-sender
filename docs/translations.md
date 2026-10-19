# Translations

English is the primary language of this project. Write source code, comments,
documentation, issues, pull requests and release notes in English. Documentation
translations are welcome as optional companions to the English version.

## Interface languages

Home Assistant selects interface text using the user's profile language. English
is the fallback; the integration does not force a different profile language.

| Language | Locale | File |
| --- | --- | --- |
| English | `en` | [en.json](../custom_components/ha_mail_sender/translations/en.json) |
| German | `de` | [de.json](../custom_components/ha_mail_sender/translations/de.json) |
| Spanish | `es` | [es.json](../custom_components/ha_mail_sender/translations/es.json) |
| French | `fr` | [fr.json](../custom_components/ha_mail_sender/translations/fr.json) |
| Italian | `it` | [it.json](../custom_components/ha_mail_sender/translations/it.json) |
| Brazilian Portuguese | `pt-BR` | [pt-BR.json](../custom_components/ha_mail_sender/translations/pt-BR.json) |
| Simplified Chinese | `zh-Hans` | [zh-Hans.json](../custom_components/ha_mail_sender/translations/zh-Hans.json) |

## Contribute or update a translation

The canonical English strings are in
[`strings.json`](../custom_components/ha_mail_sender/strings.json).
Keep `translations/en.json` identical to that file.

1. Copy `translations/en.json` to the appropriate Home Assistant locale filename.
2. Translate string values while preserving every JSON key and the full structure.
3. Preserve placeholders, product names, API identifiers and email header names
   where appropriate. Do not translate `HA Mail Sender`, `Gmail` or `Google Mail`.
4. Keep safety-related meanings precise: setup and manual reset send no email;
   acceptance by Gmail does not guarantee delivery; failed or uncertain attempts
   retain their reservation until the limit expires or the user resets it.
5. Check the translated forms, selectors and entity labels in Home Assistant when
   possible, and mention which language you reviewed in your pull request.

The current translations have complete key coverage. Fluent-speaker review and
improvements to local Home Assistant terminology are welcome.

## Documentation translations

The main [README](../README.md) and [installation guide](installation.md) are in
English. Keep translated guides under a clearly marked language directory, such as
[`docs/it/INSTALLAZIONE.md`](it/INSTALLAZIONE.md). Link them from the English guide
and keep instructions consistent when setup or delivery behavior changes.
