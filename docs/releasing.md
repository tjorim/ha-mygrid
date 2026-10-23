# Community-testing releases

The HACS package is self-contained: its device libraries are vendored from the canonical standalone package. A PyPI release is not required for community testing. Publication of this repository on GitHub is still needed for HACS custom-repository downloads; the manual-install ZIP can be used locally now.

1. Commit the reviewed library and core-overlay changes. Regenerate with `scripts/sync_hacs.py` in `ha-mygrid-core`, verify `--check`, inspect the source commit/hash provenance, and run the local validation commands from README.
2. Record the hardware checklist results; do not mark a release physically verified until those results exist. Confirm ongoing ownership and obtain manufacturer-approved brand artwork. Remove the explicit HACS `brands` exemption once artwork is included.
3. Run `scripts/build_release.py`. The ZIP includes the integration directory, vendored source and license; it excludes caches. Test it in a clean Home Assistant configuration using the minimum supported version.
4. Publish this repository under the actual GitHub owner, confirm documentation/issue URLs and repository topics, tag the version, and create release notes. The CI validates the standalone checkout and builds the ZIP; no release is published by local commands.
5. Test HACS custom-repository installation. Default HACS listing is a separate submission, not implied by custom-repository compatibility.

For core submission, use `ha-mygrid-core` and publish the independent library to PyPI first. Core does not use this vendored copy. Keep library and core sources authoritative and regenerate the HACS adaptation to prevent protocol drift. Never maintain or run two implementations of the `mygrid` domain in one Home Assistant instance.
