# Community-testing releases

The integration depends on the `mygrid-modbus` library published on PyPI; the pinned version is in `manifest.json`. Publication of this repository on GitHub is needed for HACS custom-repository downloads; the manual-install ZIP can be used locally.

1. Make sure the library version you need is on PyPI, bump the pin in `manifest.json` and the `dev` group of `pyproject.toml` (then `uv lock`), and run the local validation commands from README.
2. Record the hardware checklist results; do not mark a release physically verified until those results exist. Confirm ongoing ownership and obtain manufacturer-approved brand artwork. Remove the explicit HACS `brands` exemption once artwork is included.
3. Run `scripts/build_release.py`. The ZIP includes the integration directory and the license; it excludes caches. Test it in a clean Home Assistant configuration using the minimum supported version.
4. Publish this repository under the actual GitHub owner, confirm documentation/issue URLs and repository topics, tag the version, and create release notes. The CI validates the standalone checkout and builds the ZIP; no release is published by local commands.
5. Test HACS custom-repository installation. Default HACS listing is a separate submission, not implied by custom-repository compatibility.

A core submission would be a separate effort ported from this repository once the ModuleTwo is validated on hardware. Never run two implementations of the same domain in one Home Assistant instance.
