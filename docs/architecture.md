# Architecture and contracts

`client.py` has no Home Assistant imports. It owns one asynchronous pymodbus connection, immutable decoded snapshots, validation and a lock spanning each complete transaction sequence. Request retries and background reconnection are disabled. The next explicit read or command may connect again, but queued desired state is never retained.

The coordinator holds the shared snapshot and serializes reads and command publication. Entities subscribe through CoordinatorEntity and make no independent polling requests. All 18 registers are read together. The 12-second client operation budget bounds connect + limits + write + confirmation; each Modbus request has a 3-second timeout. A stopped peer cannot hold the lock indefinitely. Failure messages omit hostnames and raw network exceptions.

Setup and unload own the socket lifetime; config-flow probes always close temporary clients. Reconfiguration unloads the old entry before probing even a different host spelling, since two names may point at one single-client battery. Entry IDs identify devices/entities, so reconfiguration preserves identities. Hardware replacement must be handled as a new entry because the map contains no serial number.

Only `number.set_value` and `button.press` can initiate writes. No custom service, raw-register API, timer, shutdown hook or restore-state component writes to the device. A write failure may represent an applied command with a lost acknowledgment; errors tell the user this, and commands are never retried automatically. A successful setpoint response returns device state rather than an optimistic requested value.

No database migration is needed for the first release; config-entry schema version is 1. Changes to identity or stored config in later releases require a tested migration. Dependencies match the current stable Home Assistant Modbus pymodbus pin to avoid resolver conflicts. Broader minimum-version support requires running the full test suite against that version, not just lowering metadata.

The simulator is deliberately separate from client decoding and uses raw MBAP/Modbus frames. It validates address/count/unit/function and emulates device-side clamping, exception responses, dropped acknowledgments and connection exclusivity. It is not proof of firmware behavior; the physical checklist records that separately.
