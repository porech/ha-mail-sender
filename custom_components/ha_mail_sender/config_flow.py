"""Native setup and edit forms for one saved email."""

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN
from .gmail import GmailTransport
from .models import MailConfig


class MessageForms:
    """Shared form steps for setup and options, storing no OAuth secrets."""

    _values = None
    _aliases = None

    async def _account(self, user_input, step_id):
        entries = self.hass.config_entries.async_entries("google_mail")
        if not entries:
            return self.async_abort(reason="google_account_missing")
        if self._values is None:
            self._values = {}
        errors = {}
        if user_input is not None:
            self._values.update(user_input)
            try:
                if not user_input["name"].strip():
                    raise ValueError("invalid_config")
                transport = await GmailTransport.async_create(
                    self.hass, user_input["google_entry_id"]
                )
                self._aliases = await transport.async_aliases()
                if not self._aliases:
                    errors["base"] = "no_verified_senders"
                else:
                    return await self.async_step_message()
            except (ClientError, TimeoutError, HomeAssistantError, ValueError):
                errors["base"] = "cannot_connect"
        options = [{"value": e.entry_id, "label": e.title} for e in entries]
        return self.async_show_form(
            step_id=step_id,
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=self._values.get("name", "")): str,
                    vol.Required(
                        "google_entry_id",
                        default=self._values.get("google_entry_id", entries[0].entry_id),
                    ): selector.SelectSelector(selector.SelectSelectorConfig(options=options)),
                }
            ),
        )

    async def async_step_message(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._values.update(user_input)
            try:
                config = MailConfig.from_mapping(self._values)
                if config.sender not in self._aliases:
                    raise ValueError("sender_not_verified")
            except (ValueError, TypeError):
                errors["base"] = "invalid_config"
            else:
                return self.async_create_entry(title=config.name, data=self._values)
        values = self._values
        aliases = [
            {"value": address, "label": f"{name} <{address}>" if name else address}
            for address, name in self._aliases.items()
        ]
        sender = values.get("sender")
        if sender not in self._aliases:
            sender = next(iter(self._aliases))
        schema = {
            vol.Required("sender", default=sender): selector.SelectSelector(
                selector.SelectSelectorConfig(options=aliases)
            ),
            vol.Optional(
                "sender_name", default=values.get("sender_name", self._aliases[sender])
            ): str,
            vol.Required("to", default=values.get("to", "")): str,
            vol.Optional("cc", default=values.get("cc", "")): str,
            vol.Optional("bcc", default=values.get("bcc", "")): str,
            vol.Required("subject", default=values.get("subject", "")): str,
            vol.Required("body", default=values.get("body", "")): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Required("policy", default=values.get("policy", "daily")): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["daily", "interval", "none"], translation_key="policy"
                )
            ),
            vol.Required("interval_hours", default=values.get("interval_hours", 24)): vol.All(
                vol.Coerce(float), vol.Range(min=0.01, max=8760)
            ),
        }
        return self.async_show_form(
            step_id="message", data_schema=vol.Schema(schema), errors=errors
        )


class MailSenderConfigFlow(MessageForms, config_entries.ConfigFlow, domain=DOMAIN):
    """Add a named saved email."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._account(user_input, "user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MailSenderOptionsFlow()


class MailSenderOptionsFlow(MessageForms, config_entries.OptionsFlow):
    """Edit a message or deliberately release a failed reservation."""

    async def async_step_init(self, user_input=None):
        self._values = dict(self.config_entry.data) | dict(self.config_entry.options)
        return self.async_show_menu(step_id="init", menu_options=["edit", "reset"])

    async def async_step_edit(self, user_input=None):
        return await self._account(user_input, "edit")

    async def async_step_reset(self, user_input=None):
        if user_input is not None and user_input.get("confirm"):
            controller = getattr(self.config_entry, "runtime_data", None)
            if controller is None or controller.closing:
                return self.async_abort(reason="not_loaded")
            try:
                await controller.async_reset()
            except ValueError:
                return self.async_abort(reason="reset_not_allowed")
            return self.async_abort(reason="reset_complete")
        return self.async_show_form(
            step_id="reset",
            data_schema=vol.Schema(
                {
                    vol.Required("confirm", default=False): bool,
                }
            ),
        )
