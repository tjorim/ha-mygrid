# Contributing

Change integration behavior and tests here. Change protocol or device behavior in `python-mygrid-modbus`, release it to PyPI, then bump the `mygrid-modbus` pin in `manifest.json` and `pyproject.toml`.

Run the README validation commands before proposing a change. Include a redacted raw-register dump and firmware/map version for decoding issues. Never publish the battery's local address or entry identifiers. The simulator can verify most changes without hardware; clearly distinguish simulation from physical acceptance results.

Use the local manual-install ZIP or publish a HACS custom-repository release for community testing. 
