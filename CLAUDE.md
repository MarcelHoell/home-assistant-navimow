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
| `coordinator.py` | `DataUpdateCoordinator`, 30s REST poll. Owns token refresh |
| `entity.py` | `NavimowEntity` base: device info, `status` shortcut, `available` via `is_online()` |
| `lawn_mower.py`, `sensor.py`, `binary_sensor.py` | Entities, all `NavimowEntity` |
| `diagnostics.py` | Redacted config-entry dump for bug reports |

`examples/` holds copy-paste Lovelace cards. `tests/test_navimow.py` is a plain-assert script — `python3 tests/test_navimow.py`, no pytest. It also parses `lawn_mower.py`/`sensor.py` with `ast` to check the state tables agree, so it runs without Home Assistant installed. CI is just `hassfest` + `hacs` validation workflows.

## Things that will bite you

- **`coordinator.data` is `{device_id: status_dict}`**, keyed by the raw API device id. Replaced wholesale on each poll.
- **`_async_ensure_valid_token(force=False)` is the only place that refreshes tokens.** Proactive callers rely on the expiry timestamp; the reactive `TOKEN_EXPIRED` path passes `force=True`. It returns a bool and never raises — don't add a second refresh path, an earlier one drifted out of sync and re-refreshed on every poll.
- `lawn_mower._async_send_command` calls it first, since commands fail with `CODE_OAUTH_INFO_ILLEGAL` on a stale token, and raises `HomeAssistantError` when the API answers `code != 1`.
- **Entities reach into coordinator privates** (`coordinator.api`, `coordinator._async_ensure_valid_token`, `api._token`). Deliberate; don't "fix" it into an abstraction layer.
- **Raw vehicle states are Segway's, with typos** (`isIdel`). Mapped in `RAW_STATE_TO_CANONICAL` in `lawn_mower.py`; `sensor.py` has its own `_ERROR_RAW_STATES` set. Adding a state means touching both.
- **A dead refresh token raises `ConfigEntryAuthFailed`**, which opens the reauth flow. Never tell the user to remove and re-add the integration.
- **`isIdel` means the mower is switched off**, not idle. Measured against a live account: it appears within one or two polls of powering off and never once occurred while the mower was demonstrably on. `OFFLINE_RAW_STATES` in `const.py` and `RAW_STATE_TO_CANONICAL` in `lawn_mower.py` must agree — `tests/test_navimow.py` asserts it. The correctly spelled `isIdle` has never been observed and is deliberately treated as a normal idle state.
- **Station power loss is invisible.** Pulling mains from the charging station produces no state change at all.
- **The payload has exactly four fields**: `id`, `capacityRemaining`, `vehicleState`, `descriptiveCapacityRemaining`. No position, no error code, no timestamp. Anything you want to add must come from one of those four, or it cannot be built.
- **MQTT was removed in 0.8.0.** It connected and subscribed to all three `/downlink/vehicle/{id}/realtimeDate/*` topics correctly, but delivered zero messages in over four hours of logging including two mowing runs. The GPS device tracker went with it, since that channel was its only possible data source. Do not reintroduce either without a log proving messages actually arrive.
- **`binary_sensor` reports cloud reachability** via `last_update_success`, not mower state. Do not "fix" it back into a mower-online sensor.
- **Offline is not docked.** `is_online()` in `const.py` is the single reachability check; the mower entity reports `unavailable` and an unmapped `vehicleState` yields `None`, never a fake `DOCKED`.
- Battery lives at `capacityRemaining[0].rawValue`; position at `position.lat` / `position.lng`.
- Comments and some log strings are mixed Italian/English. Write new ones in English.

## Prior art, checked July 2026

Investigated whether anyone reaches data we do not. Nobody does — don't redo this.

- **`segwaynavimow/NavimowHA`** (official, v1.1.0, on `navimow-sdk`): same five endpoints plus `/openapi/smarthome/responseCommands`. Subscribes to the *identical* three MQTT topics we removed, with a source comment reading "TODO: adjust to the actual MQTT topic format" — Segway's own code is unsure they are right. Its `MowerState` declares `position`, `mowing_time`, `total_mowing_time`, `signal_strength` and `timestamp`, but those are aspirational dataclass fields, exactly like the handlers we deleted. It maps `isIdel` to `idle`, which our measurements show is wrong. It exposes a `set_blade_height` service that immediately raises "not supported via REST API". Fewer entities than this fork. **Its domain is also `navimow`, so it cannot be installed alongside this one.**
- **`TA2k/ioBroker.navimow`**: same host, same topics, no additional endpoints.
- **No map anywhere.** The app's map is not part of the OpenAPI. Only the X3 series has a genuinely open API (expansion bay, developer credentials via the app); the H3000 does not.

## Conventions

- Commit messages: Conventional Commits, English.
- Version bumps go in `manifest.json` (`version`), then a matching `vX.Y.Z` GitHub release. `hacs.json` pins the minimum HA version separately.
- Entities use `_attr_has_entity_name` + `_attr_translation_key`; names live in `translations/`, not in Python.
- User-facing strings belong in `translations/en.json`, `de.json` **and** `it.json`.
- New dependencies go in `manifest.json:requirements` — currently none, keep it that way if you can.
