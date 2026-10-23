# MyGrid ModuleTwo for Home Assistant

Local monitoring and explicit power control for **MyGrid ModuleTwo** batteries over Modbus TCP. No cloud service or account is used by the integration.

Requires **Home Assistant 2026.10.2 or newer** (Python 3.14.2+). Version 0.1.0 targets the supplied ModuleTwo register map **version 2**. The HACS package includes a generated, licensed copy of the independent **`mygrid-modbus`** device library, so testing does not require a PyPI release. The integration borrows a shared connection from Home Assistant’s Modbus integration, using `modbus-connection` and its `tmodbus` backend. Tests use Home Assistant 2026.10.2 and its exact transport dependency versions. Physical battery validation is pending; use the [acceptance checklist](docs/hardware-testing.md).

This is a community custom integration, engineered against applicable Home Assistant Platinum requirements. It has **not** received an official Home Assistant quality rating. See [quality tracking](custom_components/mygrid_modbus/quality_scale.yaml).

## Before installation

1. In the MyGrid app, set the battery's control source to **Home Assistant**. This option must already be configured for your battery. The MyGrid control source leaves the Modbus port closed.
2. Put Home Assistant and the battery on the same LAN/Wi-Fi; reserve the battery's IP address in your router.
3. For a cluster, use the **Auto leader**, never a Follow unit. Setpoints and live limits on the leader represent household totals.
4. Disconnect Modbus test programs. The battery serves **one TCP client at a time**.
5. Choose **one power controller**. Other Home Assistant integrations, app controls and Modbus writers can overwrite this integration's setpoint; the last write wins.

The protocol has no TLS or authentication. Keep it on your trusted LAN; do not forward port 502 to the internet.

## Installation

### Manual installation

The complete package is ready for manual testing now. Build or use `dist/mygrid-modbus-0.1.0.zip`, extract it into the Home Assistant configuration directory, and restart. The vendored library is included and no standalone package installation is required.

Copy the entire `custom_components/mygrid_modbus` directory into your Home Assistant configuration directory as `custom_components/mygrid_modbus`, then restart Home Assistant.

Open **Settings → Devices & services → Add integration → MyGrid ModuleTwo**. Enter:

| Field | Meaning | Default |
| --- | --- | --- |
| Host | Battery hostname or IP address, without a URL scheme | Required |
| Port | Modbus TCP port | 502 |

Unit ID is fixed to the documented value **1**. Setup reads the device and verifies its register map before creating the entry. No commands are sent during setup.

### HACS (after publishing this repository)

After this integration repository is published on GitHub, in HACS open **Custom repositories**, paste this repository's GitHub URL, choose **Integration**, then download **MyGrid ModuleTwo** and restart Home Assistant. Add MyGrid through Devices & services as above. No repository has been published by this local implementation; see [release instructions](docs/releasing.md).

## Entities

| Entity | Unit / behavior |
| --- | --- |
| State of charge | % |
| Battery power | W; positive charging, negative discharging |
| Charging power / Discharging power | W; separate nonnegative values |
| Maximum charge / discharge power | W; live limits, both positive |
| Power setpoint | W; positive charges, negative discharges; 100 W increments |
| Status | `normal`, `fault`, `telemetry_stale` |
| Stored energy | Wh, current measurement |
| Total capacity | Wh, current measurement |
| Lifetime charged / discharged energy | Wh, cumulative `total_increasing` counters |
| Problem | On for status `fault` or any set fault bit |
| Fault flags | Raw 32-bit value with `active_faults` names; disabled by default |
| Map version | Diagnostic; disabled by default |
| Individual fault indicators | All 22 documented bits; disabled by default |
| Restart | Diagnostic button; disabled by default |

Enable optional entities on the device's entity list. Fault names are described in [the register reference](docs/protocol.md). Bit 0 can mean a battery communication fault **or** a battery-system error. Unknown bits remain visible in the raw flags and trigger Problem.

When status is `telemetry_stale`, state of charge, measured/derived power, and fault indicators become **unknown**. Other valid registers remain available. A connection failure makes live measurements **unavailable**. Lifetime energy counters retain their last confirmed native values and restore saved values across entity restarts. The integration reports failures on transitions and recovers automatically as polling resumes.

### Power commands

Change **Power setpoint**, or call Home Assistant's standard `number.set_value` action. A command reads fresh limits, validates a multiple of 100 W, writes once, then reads back what the battery kept. The number shows that confirmed value, including any device-side clamp if limits changed. Limits are also bounded by the register's signed 16-bit representation.

Commands are explicit only: setup, polling, reconnect, option changes, and unloading never write power. The integration does not restore old commands, run a charging strategy, or enforce a desired setpoint. The firmware applies a setpoint about once a second; readback confirms acceptance, not actual power delivery. Check measured power and status afterward.

The manual does not specify a command watchdog or loss-of-connection fallback. **Do not assume the battery stops when Home Assistant stops.** Write zero explicitly to request idle. A failed write/readback means the command may have been applied: check current readings before deciding whether to send another command. Automatic write retries are disabled.

Restart sends `1` to register 9 once, makes cached telemetry unavailable, and resumes reads on the normal polling schedule. A battery that restarts before acknowledging may report an uncertain command; it is never automatically resent.

## Energy dashboard

Under **Settings → Dashboards → Energy**, add battery storage with **Lifetime charged energy** for energy into the battery and **Lifetime discharged energy** for energy out. Select the separate Charging power and Discharging power entities where the dashboard offers power inputs. Stored energy and Total capacity are snapshots and must not be used as cumulative energy flow.

The manual explicitly documents cluster-wide SOC, limits and setpoints. It does not establish the aggregation scope of every energy register. Confirm those totals on your cluster before relying on whole-house statistics. The protocol exposes no follower list or serial numbers; one configured leader produces one device, not invented follower devices.

## Options, updates and reconfiguration

Use the integration's **Configure** option to change polling from **5 seconds** to an integer between **2 and 300 seconds**. One function-03 request reads all 18 registers per poll. Explicit commands add fresh-limit and readback requests. Configuration changes reload the connection without writing power.

Use **Reconfigure** to change the host/port while keeping the entry's device, entities and history. Reconfiguration releases this entry’s old connection hold before probing and restores the old settings if probing fails. The manager closes a physical connection only after its last consumer releases it. Because there is no hardware identity register, aliases cannot be reliably deduplicated and replacement hardware cannot be detected. Use one address per physical endpoint; delete and recreate the entry when replacing the battery, to avoid combining histories.

Home Assistant manages one Modbus connection per canonical endpoint and serializes requests across integrations. MyGrid shares this connection; setup probes use temporary holds and entry unload releases only its own hold. Restart and command failures never explicitly disconnect another consumer. This does not allow a separate test program to share the battery’s TCP connection, and it does not arbitrate multiple writers.

No discovery, authentication, firmware updates, serial/RTU connection, or cloud API is provided by this protocol.

## Example automations

Entity IDs depend on your installation; replace the IDs below with those on your device. Positive power charges; zero requests idle. These examples run only when explicitly triggered and do not compete with another controller.

```yaml
alias: MyGrid charge at a scheduled time
triggers:
  - trigger: time
    at: "01:00:00"
conditions:
  - condition: numeric_state
    entity_id: sensor.mygrid_moduletwo_state_of_charge
    below: 80
  - condition: numeric_state
    entity_id: sensor.mygrid_moduletwo_maximum_charge_power
    above: 499
actions:
  - action: number.set_value
    target:
      entity_id: number.mygrid_moduletwo_power_setpoint
    data:
      value: 500
```

```yaml
alias: MyGrid idle at end of charge window
triggers:
  - trigger: time
    at: "05:00:00"
actions:
  - action: number.set_value
    target:
      entity_id: number.mygrid_moduletwo_power_setpoint
    data:
      value: 0
```

Fault alerts can use the Problem entity as a state trigger. Status `telemetry_stale` and unknown/unavailable entities should be handled separately from a confirmed healthy battery.

## Troubleshooting and diagnostics

| Symptom | Check |
| --- | --- |
| Cannot connect | Correct LAN/IP/port, Home Assistant control source enabled in the app, Auto leader, no competing Modbus client |
| Incompatible Modbus settings | Another consumer holds this endpoint with conflicting connection parameters; align those settings |
| Unsupported map | Only map version 2 is implemented; obtain the matching firmware manual before extending it |
| Command rejected | Multiple of 100 W, within **fresh** charge/discharge limits; negative for discharge |
| Power changes unexpectedly | Another integration, app or automation may be writing the same shared setpoint |
| Unknown measurements | Status 2 means firmware telemetry is stale; wait for status 0 or 1 |
| Unavailable | Device or network is offline; polling will reconnect without replaying commands |
| Restart command not confirmed | Firmware may have restarted before replying; check availability before retrying manually |

Download diagnostics from the integration menu. Diagnostics include decoded telemetry, update-report status and a fresh, replayable raw-register dump, with network addresses and entry identifiers omitted. An offline device reports the failure type without exposing raw exception text; an unloaded entry reports `NotLoaded`. The dump may reveal household energy usage. Diagnostic reads never issue commands.

Remove the integration under Devices & services to stop polling and release its connection hold. Home Assistant closes the physical connection when its last consumer releases it. Removal does not send a zero setpoint. Remove the HACS download (or local directory) and restart Home Assistant to uninstall it. Existing recorder history follows Home Assistant's normal retention settings.

## Development

This is the generated community-testing package for the ModuleTwo. HACS allows one integration per repository, so each MyGrid device has its own HACS repository, both generated from the same umbrella source:

| Repository | Role |
| --- | --- |
| `python-mygrid-modbus` | Standalone component-based ModuleTwo library (PyPI package `mygrid-modbus`), supplied mock-backend tests, query helper and PyPI release workflow |
| `ha-mygrid-core` | Canonical umbrella integration (domain `mygrid`, ModuleTwo and VoltBridge) shaped for Home Assistant core, plus the generator for the HACS packages |
| `ha-mygrid-modbus` | This HACS package: domain `mygrid_modbus`, generated adapter code and the byte-for-byte vendored library |
| `ha-mygrid-voltbridge` | The matching HACS package for the VoltBridge P1 meter (domain `mygrid_voltbridge`), which is a separate integration |

A checkout of this repository is self-contained for tests and installation:

```sh
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run python scripts/validate_metadata.py
uv run python scripts/build_release.py
```

The vendored files are under `custom_components/mygrid_modbus/vendor/mygrid_modbus`. The adjacent license and `origin.json` record version, source commits and per-file SHA-256 hashes. CI verifies the hashes, tests the actual vendored namespace, and runs HACS/Hassfest validation. Manufacturer-approved brand art is still pending; HACS's brand check is explicitly exempted until it is supplied. No official quality rating is claimed.

Do not edit the generated files here. To change device code, edit the sibling `python-mygrid-modbus` repository; to change integration code or tests, edit `ha-mygrid-core`. Then regenerate from `ha-mygrid-core`:

```sh
uv run python scripts/sync_hacs.py            # writes this package and the VoltBridge one
uv run python scripts/sync_hacs.py --check
```

and run `uv run python scripts/validate_metadata.py` here. The generator needs the sibling checkouts and records their Git commits. Installation, ordinary tests and metadata validation do not need them or an unpublished package. The core contribution keeps its independent PyPI requirement and the umbrella domain `mygrid`; this package uses its own domain, so it can be installed next to the VoltBridge package, but entries do not migrate to the core integration later (add the device again there).

The library tests models with the supplied mock fixtures and both actual transport backends. This package tests the integration wiring, shared sockets, energy-counter restoration and raw diagnostics. Neither controls real hardware. See [architecture](docs/architecture.md), [hardware testing](docs/hardware-testing.md), and [release instructions](docs/releasing.md).
