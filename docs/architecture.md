# Architecture

The standalone library declares the entire ModuleTwo map as a typed `Battery(Component)` under `MyGridDevice(Device)`. The planner reads registers 0–17 together; field metadata owns scaling, signed values, writable registers and low-word-first counters. Snapshot validation handles map version, SOC/status validity and telemetry staleness. Device commands own fresh-limit checks and confirmed readback, with no retries.

This integration has a single-device config flow and its own domain `mygrid_modbus`. It borrows managed units from Home Assistant's `modbus` integration and polls the device for `UpdateReport`s. It performs first refresh before forwarding platforms, derives entity availability from component status, retains lifetime counters with `RestoreSensor`, and retrieves replayable raw diagnostics. Neither the device nor the integration closes another consumer's shared connection.

The integration imports the library from PyPI (`mygrid-modbus`, pinned in `manifest.json`) and uses Home Assistant's Modbus dependency for the shared transport. Library releases use PyPI trusted publishing only when a reviewed release is explicitly triggered.

To change device behavior, change the library, release it, and bump the pin here. `scripts/validate_metadata.py` checks that the manifest and the development dependency agree.

The config-entry schema remains version 1. Identity remains entry-based because the device exposes no serial number. This transport/model refactor does not change entity keys or power sign/units. Physical acceptance remains pending; automated TCP tests use a simulator.
