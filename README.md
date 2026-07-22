<div align="center">

<img src="custom_components/navimow/brand/icon.png" alt="Navimow Integration Icon" width="128" height="128" />

# Segway Navimow for Home Assistant

Unofficial Home Assistant integration for Segway Navimow robotic lawn mowers,
built on the official Segway OpenAPI.

[![HACS Validation](https://github.com/MarcelHoell/home-assistant-navimow/actions/workflows/hacs.yml/badge.svg)](https://github.com/MarcelHoell/home-assistant-navimow/actions/workflows/hacs.yml)
[![Hassfest](https://github.com/MarcelHoell/home-assistant-navimow/actions/workflows/hassfest.yml/badge.svg)](https://github.com/MarcelHoell/home-assistant-navimow/actions/workflows/hassfest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

> [!WARNING]
> **Alpha.** Features may change and bugs are expected. Use at your own risk.

> [!NOTE]
> This is a fork of [niddu85/home-assistant-navimow](https://github.com/niddu85/home-assistant-navimow).
> The integration domain is still `navimow`, so do **not** install both at the same time.

---

## ✨ Features

- Native `lawn_mower` entity — start, pause, return to dock, live activity
- Battery level, error state, connectivity and GPS position
- **Real-time push** via MQTT over WebSockets, plus a 30 s REST poll as a safety net
- OAuth2 login through the official Navimow flow, with automatic token refresh
- Fully configured from the Home Assistant UI, no YAML required
- Localised in English, German and Italian — Home Assistant picks the language
  from each user's profile and falls back to English

## 📋 Requirements

- A Segway Navimow mower with an active Segway account
- Home Assistant 2024.1 or later
- Internet access from your Home Assistant instance

## ⚙️ Installation

### HACS (recommended)

1. HACS → ⋮ (top right) → **Custom repositories**
2. Repository: `https://github.com/MarcelHoell/home-assistant-navimow`
3. Category: **Integration** → **Add**
4. Search for *Navimow*, install it, then **restart Home Assistant**

### Manual

Copy `custom_components/navimow/` into your Home Assistant `custom_components/`
directory and restart.

## 🛠️ Setup

1. **Settings → Devices & Services → + Add Integration**
2. Search for **Navimow**
3. Give the account a name, then follow the OAuth link that opens
4. Log in with your Segway credentials and confirm — the integration picks up
   the redirect and finishes on its own

## 📱 Entities

One set per mower. `{slug}` is derived from the device name the Segway API
reports, e.g. a *Navimow H3000* becomes `navimow_h3000`.

| Entity | Description |
| --- | --- |
| `lawn_mower.{slug}` | Activity + commands. States: `mowing`, `paused`, `docked`, `returning`, `error`. Becomes `unavailable` when the mower is offline. |
| `sensor.{slug}_battery` | Battery charge in %, device class `battery` |
| `sensor.{slug}_error` | Current error code, `none` when healthy |
| `binary_sensor.{slug}_connectivity` | `on` = mower reachable |
| `device_tracker.{slug}_position` | GPS position, source type `gps` |

Not sure about your exact ids? **Developer Tools → Template**:

```jinja
{{ states | selectattr('entity_id','search','navimow')
          | map(attribute='entity_id') | list }}
```

### Actions

Standard Home Assistant lawn mower actions: `lawn_mower.start_mowing`,
`lawn_mower.pause`, `lawn_mower.dock`.

## 🖼️ Dashboard

Ready-to-paste Lovelace cards live in [`examples/`](examples/):

- [`dashboard-card.yaml`](examples/dashboard-card.yaml) — generic, replace the slug
- [`dashboard-card-h3000.yaml`](examples/dashboard-card-h3000.yaml) — concrete example

Both use core cards only — no extra frontend dependencies. Copy the file
contents into **Add card → Manual**.

## 🔄 How it works

```
OAuth2 ──► REST /authList          device list
       ──► REST /getVehicleStatus  status, polled every 30 s
       ──► MQTT over WebSockets    push updates, /downlink/vehicle/{id}/…
```

`coordinator.py` owns both channels. MQTT credentials are bound to the OAuth
token, so on disconnect the coordinator refreshes the token, refetches the
credentials and reconnects. Tokens are also refreshed proactively before
expiry and reactively on a `TOKEN_EXPIRED` response.

## 🐛 Troubleshooting

**Integration not listed after install** — restart Home Assistant, then clear
the browser cache.

**All entities `unavailable`** — the mower is powered off or unreachable. This
is expected: an offline mower is reported as unavailable rather than pretending
to be docked.

**Commands do nothing** — test with Developer Tools → Actions →
`lawn_mower.dock`. If that fails too, it is the API, not the dashboard.

**Authentication errors** — verify the Navimow phone app still works, then
remove and re-add the integration.

### Debug logging

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.navimow: debug
```

This logs the raw `authList` / `getVehicleStatus` responses and every MQTT
payload — attach those (redact tokens and serial numbers) when reporting a bug.

## 🧪 Development

```bash
python3 tests/test_is_online.py
```

Raw vehicle states come from Segway and include typos (`isIdel`). They are
mapped in `RAW_STATE_TO_CANONICAL` in `lawn_mower.py`; `sensor.py` keeps its
own `_ERROR_RAW_STATES` set. Adding a state means touching both.

## 🤝 Contributing

Issues and pull requests welcome. Fixes that are not specific to this fork are
best sent upstream to
[niddu85/home-assistant-navimow](https://github.com/niddu85/home-assistant-navimow).

## 📜 Disclaimer

**Unofficial** project, not affiliated with, endorsed by or sponsored by
Segway or Navimow. It uses the OpenAPI that Segway provides, but the
implementation is community maintained.

## 📝 License

MIT — see [LICENSE](LICENSE).

## 📚 References

- [Segway Navimow](https://www.segway.com/navimow/)
- [Home Assistant `lawn_mower` integration](https://www.home-assistant.io/integrations/lawn_mower/)
- [Home Assistant developer docs](https://developers.home-assistant.io/)
