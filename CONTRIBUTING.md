# Contributing

Change protocol behavior in `mygrid-modbus` and integration behavior/tests in `ha-mygrid-core`, then regenerate this repository with `scripts/sync_hacs.py` (run in `ha-mygrid-core`). The HACS source and vendored files are generated; hand edits will be overwritten.

Run the README validation commands before proposing a change. Include a redacted raw-register dump and firmware/map version for decoding issues. Never publish the battery's local address or entry identifiers. The simulator can verify most changes without hardware; clearly distinguish simulation from physical acceptance results.

Use the local manual-install ZIP or publish a HACS custom-repository release for community testing. A core contribution follows the separate overlay instructions and requires the independently published library.
