# wger Home Assistant Integration

A custom integration for [Home Assistant](https://www.home-assistant.io/) that exposes data
from a [wger](https://wger.de) Workout Manager instance as sensors. Works with both the
public `wger.de` instance and self-hosted deployments.

## Features

- Configuration via the UI (no YAML required)
- Works with the hosted instance (`https://wger.de`) or any self-hosted URL
- Uses a personal API token (`Authorization: Token …`)
- Polls the API every 15 minutes by default

### Sensors created per configured account

| Sensor | Description |
| ------ | ----------- |
| `sensor.wger_latest_weight` | Most recent body-weight log entry (kg) |
| `sensor.wger_workouts` | Total number of defined workouts |
| `sensor.wger_workout_sessions` | Total number of logged workout sessions |
| `sensor.wger_last_session` | Date of the most recent workout session |
| `sensor.wger_nutrition_plans` | Number of nutrition plans on the account |

## Installation (HACS)

1. In HACS → **Integrations** → ⋮ → **Custom repositories**, add this repo as type
   *Integration*.
2. Search for **wger Workout Manager** in HACS and install it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and pick **wger**.

## Manual installation

Copy `custom_components/wger/` into your Home Assistant `config/custom_components/`
directory and restart Home Assistant.

## Configuration

You will be asked for:

- **Server URL** – defaults to `https://wger.de`. For a self-hosted instance, enter the
  full base URL (e.g. `https://wger.example.com`).
- **API key** – generate one in wger under *Settings → API*.
- **Verify SSL certificate** – disable only for self-hosted servers with self-signed
  certificates.

The integration validates credentials by calling `/api/v2/userprofile/`.

## Notes

- Only public read endpoints are used; the integration never modifies your wger data.
- Rename the entities in the UI to suit your dashboards.
