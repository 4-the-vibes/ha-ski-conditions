"""Config and options flow for Ski Conditions."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import (
    CONF_RESORTS,
    CONF_SOURCES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    RESORTS,
    STEP_UPDATE_INTERVAL,
)


def _schema(resorts: list[str], interval: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_RESORTS, default=resorts): SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=k, label=r.name) for k, r in RESORTS.items()],
                    multiple=True,
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL, default=interval): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL,
                    max=MAX_UPDATE_INTERVAL,
                    step=STEP_UPDATE_INTERVAL,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )


class SkiConditionsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_RESORTS]:
                errors[CONF_RESORTS] = "no_resorts"
            else:
                return self.async_create_entry(
                    title="Ski Conditions",
                    data={},
                    options={
                        CONF_RESORTS: user_input[CONF_RESORTS],
                        CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    },
                )
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(list(RESORTS), DEFAULT_UPDATE_INTERVAL),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SkiConditionsOptionsFlow()


class SkiConditionsOptionsFlow(OptionsFlow):
    """Pick resorts/interval, then optionally override source page slugs."""

    def __init__(self) -> None:
        self._pending: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        opts = self.config_entry.options
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_RESORTS]:
                errors[CONF_RESORTS] = "no_resorts"
            else:
                self._pending = {
                    CONF_RESORTS: user_input[CONF_RESORTS],
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                }
                return await self.async_step_sources()
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                opts.get(CONF_RESORTS, list(RESORTS)),
                int(opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)),
            ),
            errors=errors,
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = self.config_entry.options.get(CONF_SOURCES, {})
        resorts = self._pending[CONF_RESORTS]
        if user_input is not None:
            sources: dict[str, dict[str, str]] = {}
            for rid in resorts:
                r = RESORTS[rid]
                ots = (user_input.get(f"{rid}_onthesnow") or "").strip()
                sf = (user_input.get(f"{rid}_snowforecast") or "").strip()
                override = {}
                if ots != r.onthesnow:
                    override["onthesnow"] = ots or " "  # blank => disable source
                if sf != r.snowforecast:
                    override["snowforecast"] = sf or " "
                if override:
                    sources[rid] = override
            return self.async_create_entry(data={**self._pending, CONF_SOURCES: sources})

        fields: dict[Any, Any] = {}
        for rid in resorts:
            r = RESORTS[rid]
            ov = current.get(rid, {})
            fields[vol.Optional(f"{rid}_onthesnow", default=(ov.get("onthesnow") or r.onthesnow).strip())] = TextSelector()
            fields[vol.Optional(f"{rid}_snowforecast", default=(ov.get("snowforecast") or r.snowforecast).strip())] = TextSelector()
        return self.async_show_form(step_id="sources", data_schema=vol.Schema(fields))
