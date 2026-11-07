# Ski Conditions for Home Assistant

Snow reports, current mountain weather and a 24-hour and 7-day forecast for:
**Sunshine Village, Lake Louise, Panorama, Kicking Horse, Fernie and Castle Mountain**.

No API keys and no extra Python packages.

## Install

**HACS (custom repository):** push this folder to a GitHub repo. In HACS, go to ⋮ → Custom repositories, add the repo URL as type *Integration*, install it, then restart HA.

**Manual:** copy `custom_components/ski_conditions` into your HA `config/custom_components/` folder and restart.

Then go to **Settings → Devices & services → Add integration → Ski Conditions**. Pick your resorts and the update interval.

Requires Home Assistant 2025.1 or newer.

## Where the data comes from

| Data | Source | Notes |
|---|---|---|
| Base and summit depth, 24/48/72 h snowfall, lifts and runs open, surface, open/closed | **OnTheSnow** (resort-reported) | Used first |
| Fresh snow ("powder depth"), last snowfall, and backup base and summit depth | **Snow-Forecast.com** (resort-reported) | Fills any gaps |
| Current temperature (summit and base), wind, gusts, direction, freezing level, hourly and daily forecast | **Open-Meteo** | A model forecast at each resort's summit and base elevation, fetched in one request for all resorts |

If no resort report has a 24 h snowfall figure (for example before the season opens), **Snowfall 24h** uses the Open-Meteo model estimate. Its `source` attribute says which one you're seeing.

OnTheSnow and Snow-Forecast don't offer public APIs, so their pages are parsed. If a site changes its layout, check that resort's **Data status** sensor. Its attributes show the error and any parse notes, and the other sources keep working.

## Entities

Each resort gets its own device (for example `Sunshine Village`) with:

- **Reported snow:** Base depth, Summit depth, Powder depth, Snowfall 24h / 48h / 72h, Last snowfall, Lifts open, Runs open, Surface conditions, Resort status, Report date
- **Current weather:** Summit temperature, Base temperature, Summit feels like, Summit wind, Summit wind gust, Base wind, Summit wind direction, Freezing level, Snowfall past 24h (model)
- **Forecast:** Forecast snowfall next 24h, Forecast high / low next 24h, Forecast max wind / gust next 24h, Forecast precipitation chance next 24h, Forecast max freezing level next 24h, Forecast next 24h (a text summary, with an `hourly` attribute), Forecast snowfall 7 days (with a `by_day` attribute)
- **Weather entity** `weather.<resort>_summit_weather`, with 48 h hourly and 7-day daily forecasts. It works with the standard Weather forecast card.
- **Data status** (diagnostic): `ok`, `partial` or `error`, with the last success time for each source

The **Ski Conditions** hub device has:

- **Update interval** (`number.ski_conditions_update_interval`): 10–1440 minutes. Changes apply immediately, with no restart or reload. You can also change it from **Configure**, and it can be set from automations, for example faster polling on storm days.
- **Refresh now** (`button.ski_conditions_refresh_now`)

Depths are stored in cm, and HA converts them if your system uses imperial units.

## Fixing a source page

If a resort's **Data status** shows HTTP 404 for one source, the site probably renamed its page. Go to **Configure → Next** and enter the correct identifier:

- OnTheSnow: the part in `onthesnow.com/<path>/skireport`, for example `alberta/lake-louise`
- Snow-Forecast: the part in `snow-forecast.com/resorts/<slug>/snow-report`, for example `Lake-Louise`

Clear a field to turn that source off for a resort.

## Examples

`examples/dashboard.yaml` has a dashboard view. `examples/automations.yaml` has a powder-day alert and a storm-mode polling rule.

## Development

`pytest tests` runs the parser tests. They don't need Home Assistant installed.
