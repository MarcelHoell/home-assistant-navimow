# CLAUDE.md

Unofficial Home Assistant custom integration for Segway Navimow robot mowers, via the Segway OpenAPI (`navimow-fra.ninebot.com`). Alpha. HACS-installable.

Fork of `niddu85/home-assistant-navimow`. `origin` = this fork, `upstream` = the original. Domain stays `navimow` deliberately — renaming it would force a re-setup of the integration.

## Layout

Everything lives in `custom_components/navimow/`:

| File | Role |
| --- | --- |
| `const.py` | Domain, hardcoded OAuth client id/secret, token + auth URLs, `is_online()` |
| `config_flow.py` | 3 steps: account name → OAuth link → code exchange. Registers `/api/navimow/callback` view to catch the redirect |
| `api.py` | REST client: `authList`, `getVehicleStatus`, `sendCommands`, `mqtt/userInfo/get/v2`, token refresh. Read errors return `None` / `{"error": "TOKEN_EXPIRED"}` — never raise; `async_send_command` returns the raw response dict instead |
| `coordinator.py` | `DataUpdateCoordinator`, 30s poll + paho-mqtt-over-websockets push. Owns token refresh and MQTT credential re-auth |
| `entity.py` | `NavimowEntity` base: device info, `status` shortcut, `available` via `is_online()` |
| `lawn_mower.py`, `sensor.py`, `binary_sensor.py`, `device_tracker.py` | Entities, all `NavimowEntity` |
| `diagnostics.py` | Redacted config-entry dump for bug reports |

`examples/` holds copy-paste Lovelace cards. `tests/test_navimow.py` is a plain-assert script — `python3 tests/test_navimow.py`, no pytest. It also parses `lawn_mower.py`/`sensor.py` with `ast` to check the state tables agree, so it runs without Home Assistant installed. CI is just `hassfest` + `hacs` validation workflows.

## Things that will bite you

- **`coordinator.data` is `{device_id: status_dict}`**, keyed by the raw API device id. MQTT handlers mutate it in place then call `async_set_updated_data`.
- **`_async_ensure_valid_token(force=False)` is the only place that refreshes tokens.** Proactive callers rely on the expiry timestamp; the reactive `TOKEN_EXPIRED` path passes `force=True`. It returns a bool and never raises — don't add a second refresh path, an earlier one drifted out of sync and re-refreshed on every poll.
- `lawn_mower._async_send_command` calls it first, since commands fail with `CODE_OAUTH_INFO_ILLEGAL` on a stale token, and raises `HomeAssistantError` when the API answers `code != 1`.
- **MQTT creds are bound to the OAuth token.** On disconnect the coordinator refreshes the token, refetches MQTT creds, and reconnects with new websocket auth headers.
- **Entities reach into coordinator privates** (`coordinator.api`, `coordinator._async_ensure_valid_token`, `api._token`). Deliberate; don't "fix" it into an abstraction layer.
- **Raw vehicle states are Segway's, with typos** (`isIdel`). Mapped in `RAW_STATE_TO_CANONICAL` in `lawn_mower.py`; `sensor.py` has its own `_ERROR_RAW_STATES` set. Adding a state means touching both.
- **The coordinator owns the MQTT client's lifetime.** `async_shutdown()` stops it on unload; without that a reload leaves an orphan client reconnecting forever into dead data.
- **A dead refresh token raises `ConfigEntryAuthFailed`**, which opens the reauth flow. Never tell the user to remove and re-add the integration.
- **`isIdel` means the mower is switched off**, not idle. Measured against a live account: it appears within one or two polls of powering off and never once occurred while the mower was demonstrably on. `OFFLINE_RAW_STATES` in `const.py` and `RAW_STATE_TO_CANONICAL` in `lawn_mower.py` must agree — `tests/test_navimow.py` asserts it. The correctly spelled `isIdle` has never been observed and is deliberately treated as a normal idle state.
- **Station power loss is invisible.** Pulling mains from the charging station produces no state change at all.
- **The payload has exactly four fields**: `id`, `capacityRemaining`, `vehicleState`, `descriptiveCapacityRemaining`. No position, no error code, no timestamp — `device_tracker` and the error sensor depend entirely on MQTT, which has never delivered a single message in over four hours of logs, mowing included.
- **`binary_sensor` reports cloud reachability** via `last_update_success`, not mower state. Do not "fix" it back into a mower-online sensor.
- **Offline is not docked.** `is_online()` in `const.py` is the single reachability check; the mower entity reports `unavailable` and an unmapped `vehicleState` yields `None`, never a fake `DOCKED`.
- Battery lives at `capacityRemaining[0].rawValue`; position at `position.lat` / `position.lng`.
- Comments and some log strings are mixed Italian/English. Write new ones in English.

## Conventions

- Commit messages: Conventional Commits, English.
- Version bumps go in `manifest.json` (`version`), then a matching `vX.Y.Z` GitHub release. `hacs.json` pins the minimum HA version separately.
- Entities use `_attr_has_entity_name` + `_attr_translation_key`; names live in `translations/`, not in Python.
- User-facing strings belong in `translations/en.json`, `de.json` **and** `it.json`.
- New dependencies go in `manifest.json:requirements` — currently only `paho-mqtt`.
