# Ski Conditions for Home Assistant

Snow reports, current mountain weather and a 24-hour and 7-day forecast for **any ski resort**. It comes with a searchable list of about 190 resorts across Canada and the western US, and you can add any other resort yourself.

No API keys and no extra Python packages.

## Install

**HACS (custom repository):** in HACS, go to ⋮ → Custom repositories, add this repo's URL as type *Integration*, install it, then restart HA.

**Manual:** copy `custom_components/ski_conditions` into your HA `config/custom_components/` folder and restart.

Requires **Home Assistant 2025.6 or newer**.

## Setup

1. Go to **Settings → Devices & services → Add integration → Ski Conditions**.
2. Optionally pick some resorts to start with (type to search the dropdown), and choose an update interval.

### Adding, editing and removing resorts

Each resort is its own entry under the integration:

- **Add:** on the integration's page, click **Add resort**, then type to search. Pick **➕ Custom resort** at the top to add one that isn't listed.
- **Edit:** use the resort's ⋮ menu → **Reconfigure**. You can change its name, coordinates, elevations or source pages.
- **Remove:** use the resort's ⋮ menu → **Delete**. Its device and entities go with it.

When you add or edit a resort, the integration **test-loads its OnTheSnow and Snow-Forecast pages** and shows what it found, for example "✅ base 45 cm, lifts 3/7" or "❌ HTTP 404". Fix a page name there, or clear it to skip that source. Weather and forecasts don't depend on either page.

### Custom resorts

You need:

- **Name, latitude and longitude, and base and summit elevation in metres.** These position the weather forecast. Any map app gives coordinates, and the resort's website or Wikipedia has elevations.
- **Optional:** the resort's **OnTheSnow** path, the part in `onthesnow.com/<path>/skireport` (for example `alberta/lake-louise`), and its **Snow-Forecast** slug, the part in `snow-forecast.com/resorts/<slug>/snow-report` (for example `Lake-Louise`).

## Where the data comes from

| Data | Source | Notes |
|---|---|---|
| Base and summit depth, 24/48/72 h snowfall, lifts and runs open, surface, open/closed | **OnTheSnow** (resort-reported) | Used first |
| Fresh snow ("powder depth"), last snowfall, and backup base and summit depth | **Snow-Forecast.com** (resort-reported) | Fills any gaps |
| Current temperature (summit and base), wind, gusts, direction, freezing level, hourly and daily forecast | **Open-Meteo** | A model forecast at each resort's summit and base elevation, batched into as few requests as possible |

If no resort report has a 24 h snowfall figure (for example before the season opens), **Snowfall 24h** uses the Open-Meteo model estimate. Its `source` attribute says which one you're seeing.

**About the built-in list:**

- **OnTheSnow page names** come from OnTheSnow's own province and state listings, except Arizona and Alaska.
- **Snow-Forecast names** for Alberta, BC and Colorado come from Snow-Forecast's listings. The rest follow the site's usual pattern and may need a fix in the add-resort test step.
- **Coordinates and elevations** are approximate.

## Entities

Each resort gets its own device (for example `Sunshine Village`) with:

- **Reported snow:** Base depth, Summit depth, Powder depth, Snowfall 24h / 48h / 72h, Last snowfall, Lifts open, Runs open, Surface conditions, Resort status, Report date
- **Current weather:** Summit temperature, Base temperature, Summit feels like, Summit wind, Summit wind gust, Base wind, Summit wind direction, Freezing level, Snowfall past 24h (model)
- **Forecast:** Forecast snowfall next 24h, Forecast high / low next 24h, Forecast max wind / gust next 24h, Forecast precipitation chance next 24h, Forecast max freezing level next 24h, Forecast next 24h (a text summary, with an `hourly` attribute), Forecast snowfall 7 days (with a `by_day` attribute)
- **Weather entity** `weather.<resort>_summit_weather`, with 48 h hourly and 7-day daily forecasts
- **Data status** (diagnostic): `ok`, `partial` or `error`, with the last success time for each source

The **Ski Conditions** hub device has:

- **Update interval** (`number.ski_conditions_update_interval`): 10–1440 minutes. Changes apply immediately, and it can be set from automations. You can also change it with **Configure** on the integration.
- **Refresh now** (`button.ski_conditions_refresh_now`)

Depths are stored in cm, and HA converts them if your system uses imperial units.

## Upgrading from 1.x

Your existing resorts are converted to individual resort entries automatically. Any page names you customised are kept, and so are your entity IDs, so dashboards and automations keep working.

## Examples

`examples/dashboard.yaml` has a dashboard view for 8 Rockies resorts; edit the resort names to match yours. `examples/automations.yaml` has a powder-day alert and a storm-mode polling rule. Both automations work with whatever resorts you've added.

## Development

`pytest tests` runs the parser and catalog tests. They don't need Home Assistant installed.
