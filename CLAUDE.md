# CLAUDE.md

Unofficial Home Assistant custom integration for Segway Navimow robot mowers, via the Segway OpenAPI (`navimow-fra.ninebot.com`). Alpha. HACS-installable.

## Layout

Everything lives in `custom_components/navimow/`:

| File | Role |
|---|---|
| `const.py` | Domain, hardcoded OAuth client id/secret, token + auth URLs |
| `config_flow.py` | 3 steps: account name → OAuth link → code exchange. Registers `/api/navimow/callback` view to catch the redirect |
| `api.py` | REST client: `authList`, `getVehicleStatus`, `sendCommands`, `mqtt/userInfo/get/v2`, token refresh. API errors return `None` / `{"error": "TOKEN_EXPIRED"}` — never raises |
| `coordinator.py` | `DataUpdateCoordinator`, 30s poll + paho-mqtt-over-websockets push. Owns token refresh and MQTT credential re-auth |
| `lawn_mower.py`, `sensor.py`, `binary_sensor.py`, `device_tracker.py` | Entities, all `CoordinatorEntity` |

No tests, no lint config. CI is just `hassfest` + `hacs` validation workflows.

## Things that will bite you

- **`coordinator.data` is `{device_id: status_dict}`**, keyed by the raw API device id. MQTT handlers mutate it in place then call `async_set_updated_data`.
- **Token refresh happens in two places** — proactively in `_async_update_data` (expiry timestamp + 10s buffer) and reactively on a `TOKEN_EXPIRED` response. `lawn_mower._async_send_command` also calls `_async_ensure_valid_token()` first, since commands fail with `CODE_OAUTH_INFO_ILLEGAL` on a stale token.
- **MQTT creds are bound to the OAuth token.** On disconnect the coordinator refreshes the token, refetches MQTT creds, and reconnects with new websocket auth headers.
- **Entities reach into coordinator privates** (`coordinator.api`, `coordinator._async_ensure_valid_token`, `api._token`). Deliberate; don't "fix" it into an abstraction layer.
- **Raw vehicle states are Segway's, with typos** (`isIdel`). Mapped in `RAW_STATE_TO_CANONICAL` in `lawn_mower.py`; `sensor.py` has its own `_ERROR_RAW_STATES` set. Adding a state means touching both.
- Battery lives at `capacityRemaining[0].rawValue`; position at `position.lat` / `position.lng`.
- Comments and some log strings are mixed Italian/English. Write new ones in English.

## Conventions

- Version bumps go in `manifest.json` (`version`). `hacs.json` pins the minimum HA version separately.
- User-facing strings belong in `translations/en.json` **and** `it.json`.
- New dependencies go in `manifest.json:requirements` — currently only `paho-mqtt`.
