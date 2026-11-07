"""Weather entities (with hourly + daily forecast) for each resort's summit."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, UTC

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfLength, UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import ResortEntity

HOURLY_HOURS = 48


def wmo_to_condition(code: int | None, is_day: bool = True) -> str | None:
    """Map WMO weather codes (Open-Meteo) to Home Assistant conditions."""
    if code is None:
        return None
    if code == 0:
        return "sunny" if is_day else "clear-night"
    if code in (1, 2):
        return "partlycloudy"
    if code == 3:
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 61, 63, 80, 81):
        return "rainy"
    if code in (65, 82):
        return "pouring"
    if code in (56, 57, 66, 67):
        return "snowy-rainy"
    if code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    if code in (95, 96, 99):
        return "lightning-rainy"
    return None


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ResortWeather(coordinator, rid) for rid in coordinator.resort_ids)


class ResortWeather(ResortEntity, SingleCoordinatorWeatherEntity):
    """Summit weather + forecast from Open-Meteo."""

    _attr_name = "Summit weather"
    _attr_attribution = "Weather data by Open-Meteo.com"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator, resort_id: str) -> None:
        super().__init__(coordinator, resort_id, "weather")

    @property
    def _cur(self) -> dict:
        st = self.state_data
        return st.weather.summit_current if st and st.weather else {}

    @property
    def condition(self) -> str | None:
        c = self._cur
        return wmo_to_condition(c.get("weather_code"), bool(c.get("is_day", 1)))

    @property
    def native_temperature(self) -> float | None:
        return self._cur.get("temperature_2m")

    @property
    def native_apparent_temperature(self) -> float | None:
        return self._cur.get("apparent_temperature")

    @property
    def humidity(self) -> float | None:
        return self._cur.get("relative_humidity_2m")

    @property
    def cloud_coverage(self) -> float | None:
        return self._cur.get("cloud_cover")

    @property
    def native_wind_speed(self) -> float | None:
        return self._cur.get("wind_speed_10m")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._cur.get("wind_gusts_10m")

    @property
    def wind_bearing(self) -> float | None:
        return self._cur.get("wind_direction_10m")

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        st = self.state_data
        if not st or not st.weather:
            return None
        now = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
        out: list[Forecast] = []
        for h in st.weather.hourly:
            if h["datetime"] < now:
                continue
            if len(out) >= HOURLY_HOURS:
                break
            out.append(Forecast(
                datetime=h["datetime"].astimezone(UTC).isoformat(),
                condition=wmo_to_condition(h.get("weather_code"), bool(h.get("is_day", 1))),
                native_temperature=h.get("temperature_2m"),
                native_apparent_temperature=h.get("apparent_temperature"),
                native_precipitation=h.get("precipitation"),
                precipitation_probability=h.get("precipitation_probability"),
                native_wind_speed=h.get("wind_speed_10m"),
                native_wind_gust_speed=h.get("wind_gusts_10m"),
                wind_bearing=h.get("wind_direction_10m"),
                humidity=h.get("relative_humidity_2m"),
                cloud_coverage=h.get("cloud_cover"),
            ))
        return out

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        st = self.state_data
        if not st or not st.weather:
            return None
        tz = timezone(timedelta(seconds=st.weather.utc_offset))
        today = dt_util.utcnow().astimezone(tz).date()
        out: list[Forecast] = []
        for d in st.weather.daily:
            day = datetime.fromisoformat(d["time"]).replace(tzinfo=tz)
            if day.date() < today:
                continue
            out.append(Forecast(
                datetime=day.astimezone(UTC).isoformat(),
                condition=wmo_to_condition(d.get("weather_code")),
                native_temperature=d.get("temperature_2m_max"),
                native_templow=d.get("temperature_2m_min"),
                native_precipitation=d.get("precipitation_sum"),
                precipitation_probability=d.get("precipitation_probability_max"),
                native_wind_speed=d.get("wind_speed_10m_max"),
                native_wind_gust_speed=d.get("wind_gusts_10m_max"),
                wind_bearing=d.get("wind_direction_10m_dominant"),
            ))
        return out
