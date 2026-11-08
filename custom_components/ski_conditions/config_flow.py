"""Config, options and per-resort sub-entry flows for Ski Conditions."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.util import slugify

from .api import test_source
from .catalog import CATALOG, catalog_label, sorted_catalog
from .const import (
    CONF_RESORTS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    STEP_UPDATE_INTERVAL,
    SUBENTRY_RESORT,
    Resort,
)

CONF_RESORT = "resort"
CUSTOM = "__custom__"
CONF_TEST_AGAIN = "test_again"


def _interval_selector() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL, step=STEP_UPDATE_INTERVAL,
            unit_of_measurement="min", mode=NumberSelectorMode.BOX,
        )
    )


def _catalog_options(exclude: set[str], custom: bool) -> list[SelectOptionDict]:
    opts = [SelectOptionDict(value=CUSTOM, label="➕ Custom resort (enter details yourself)")] if custom else []
    opts += [
        SelectOptionDict(value=r.id, label=catalog_label(r))
        for r in sorted_catalog()
        if r.id not in exclude
    ]
    return opts


# --------------------------------------------------------------------------- #
# Main entry (hub): pick any number of catalog resorts + interval
# --------------------------------------------------------------------------- #
class SkiConditionsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            # The initial picks are turned into resort sub-entries on first setup.
            return self.async_create_entry(
                title="Ski Conditions",
                data={},
                options={
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_RESORTS: [i for i in user_input.get(CONF_RESORTS, []) if i in CATALOG],
                },
            )
        schema = vol.Schema(
            {
                vol.Optional(CONF_RESORTS, default=[]): SelectSelector(
                    SelectSelectorConfig(
                        options=_catalog_options(set(), custom=False),
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): _interval_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SkiConditionsOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_RESORT: ResortSubentryFlow}


class SkiConditionsOptionsFlow(OptionsFlow):
    """Hub options: just the update interval (resorts are managed as sub-entries)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            opts = {k: v for k, v in self.config_entry.options.items() if k != CONF_RESORTS}
            return self.async_create_entry(
                data={**opts, CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL])}
            )
        current = int(self.config_entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_UPDATE_INTERVAL, default=current): _interval_selector()}),
        )


# --------------------------------------------------------------------------- #
# Resort sub-entry: add (catalog or custom) and reconfigure
# --------------------------------------------------------------------------- #
def _details_schema(r: Resort | None, *, with_name: bool = True) -> vol.Schema:
    def d(attr: str, fallback: Any = vol.UNDEFINED) -> Any:
        return getattr(r, attr) if r is not None else fallback

    fields: dict[Any, Any] = {}
    if with_name:
        fields[vol.Required("name", default=d("name"))] = TextSelector()
    fields[vol.Required("latitude", default=d("latitude"))] = NumberSelector(
        NumberSelectorConfig(min=-90, max=90, step="any", mode=NumberSelectorMode.BOX))
    fields[vol.Required("longitude", default=d("longitude"))] = NumberSelector(
        NumberSelectorConfig(min=-180, max=180, step="any", mode=NumberSelectorMode.BOX))
    fields[vol.Required("base_elevation", default=d("base_elevation"))] = NumberSelector(
        NumberSelectorConfig(min=-100, max=6000, step=1, unit_of_measurement="m", mode=NumberSelectorMode.BOX))
    fields[vol.Required("summit_elevation", default=d("summit_elevation"))] = NumberSelector(
        NumberSelectorConfig(min=-100, max=6000, step=1, unit_of_measurement="m", mode=NumberSelectorMode.BOX))
    fields[vol.Optional("onthesnow", default=d("onthesnow", ""))] = TextSelector()
    fields[vol.Optional("snowforecast", default=d("snowforecast", ""))] = TextSelector()
    return vol.Schema(fields)


def _icon(ok: bool | None) -> str:
    return {True: "✅", False: "❌", None: "➖"}[ok]


class ResortSubentryFlow(ConfigSubentryFlow):
    """Add or edit one resort."""

    def __init__(self) -> None:
        self._resort: Resort | None = None
        self._reconfiguring = False

    # ---- helpers ------------------------------------------------------------ #
    def _taken_ids(self) -> set[str]:
        return {s.unique_id for s in self._get_entry().subentries.values() if s.unique_id}


    # ---- add: choose from catalog or custom ---------------------------------- #
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        taken = self._taken_ids()
        if user_input is not None:
            choice = user_input[CONF_RESORT]
            if choice == CUSTOM:
                return await self.async_step_custom()
            if choice not in CATALOG:
                errors[CONF_RESORT] = "unknown_resort"
            elif choice in taken:
                return self.async_abort(reason="already_configured")
            else:
                self._resort = CATALOG[choice]
                return await self.async_step_sources()
        schema = vol.Schema(
            {
                vol.Required(CONF_RESORT): SelectSelector(
                    SelectSelectorConfig(
                        options=_catalog_options(taken, custom=True),
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,  # renders a type-to-filter combo box
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_custom(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input["name"]).strip()
            rid = f"custom_{slugify(name)}"
            if not name or not slugify(name):
                errors["name"] = "invalid_name"
            elif rid in self._taken_ids() or rid in CATALOG:
                errors["name"] = "name_in_use"
            elif user_input["summit_elevation"] < user_input["base_elevation"]:
                errors["summit_elevation"] = "summit_below_base"
            else:
                self._resort = Resort.from_dict({**user_input, "id": rid, "name": name})
                return await self.async_step_sources()
        return self.async_show_form(
            step_id="custom", data_schema=_details_schema(None), errors=errors
        )

    # ---- reconfigure: edit everything except the id -------------------------- #
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        self._reconfiguring = True
        subentry = self._get_reconfigure_subentry()
        current = Resort.from_dict(dict(subentry.data))
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input["summit_elevation"] < user_input["base_elevation"]:
                errors["summit_elevation"] = "summit_below_base"
            else:
                self._resort = Resort.from_dict({**current.to_dict(), **user_input})
                return await self.async_step_sources()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_details_schema(current),
            errors=errors,
            description_placeholders={"resort": current.name},
        )

    # ---- shared: test the two source pages, allow corrections ---------------- #
    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        assert self._resort is not None
        r = self._resort
        if user_input is not None:
            ots = (user_input.get("onthesnow") or "").strip()
            sf = (user_input.get("snowforecast") or "").strip()
            changed = (ots, sf) != (r.onthesnow, r.snowforecast)
            self._resort = r = Resort.from_dict({**r.to_dict(), "onthesnow": ots, "snowforecast": sf})
            if not changed and not user_input.get(CONF_TEST_AGAIN):
                return self._finish(r)

        session = async_get_clientsession(self.hass)
        ots_ok, ots_msg = await test_source(session, "onthesnow", r.onthesnow)
        sf_ok, sf_msg = await test_source(session, "snowforecast", r.snowforecast)
        schema = vol.Schema(
            {
                vol.Optional("onthesnow", default=r.onthesnow): TextSelector(),
                vol.Optional("snowforecast", default=r.snowforecast): TextSelector(),
                vol.Optional(CONF_TEST_AGAIN, default=False): bool,
            }
        )
        return self.async_show_form(
            step_id="sources",
            data_schema=schema,
            description_placeholders={
                "resort": r.name,
                "ots_icon": _icon(ots_ok),
                "ots_msg": ots_msg,
                "sf_icon": _icon(sf_ok),
                "sf_msg": sf_msg,
            },
            last_step=True,
        )

    def _finish(self, r: Resort) -> SubentryFlowResult:
        if self._reconfiguring:
            return self.async_update_and_abort(
                self._get_entry(), self._get_reconfigure_subentry(), title=r.name, data=r.to_dict()
            )
        return self.async_create_entry(title=r.name, data=r.to_dict(), unique_id=r.id)
