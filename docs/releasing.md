# Releasing

This delivery creates two local Git repositories: this integration and the sibling `mygrid-modbus` protocol library. HACS installation from a custom repository becomes possible after a maintainer publishes it on GitHub.

1. Release **`mygrid-modbus==0.1.0` to PyPI first**, following its own release instructions. Verify installation into an empty environment. Then remove the development-only `[tool.uv.sources]` override here, run `uv lock --no-sources`, remove CI’s companion-library checkout, and test with the published package. Normal HACS installation and Home Assistant core cannot use an unpublished sibling checkout.
2. Confirm the GitHub owner/repository and maintainer. Manifest links and `codeowners` are prepared for `tjorim/ha-mygrid`, based on the connected GitHub account; these links will become live only if the local repository is published there. If publishing elsewhere, update `documentation`, `issue_tracker` and `codeowners` first. No remote repository was created.
3. Add a GitHub repository description and suitable `home-assistant`, `hacs`, `mygrid`, and `modbus` topics. Keep the repository layout as shipped: `custom_components/mygrid`.
4. Run the locked development commands in README. CI enforces lint, formatting, strict types, at least 95% branch-aware coverage, local metadata validation and HACS validation. HACS's remote action needs a real GitHub repository and cannot be fully verified locally.
5. Complete and record the hardware checklist; document any firmware or cluster limitations. Do not label the release physically verified until results exist.
6. Review every `quality_scale.yaml` entry and evidence, especially the unresolved maintainer/branding items. Official Platinum grading is unavailable to a standalone custom integration; do not set a misleading manifest rating.
7. Keep `manifest.json` and `pyproject.toml` versions aligned. Tag `v0.1.0`, create GitHub release notes describing compatibility and known limitations, and publish the repository.
8. Test HACS custom-repository installation in a clean Home Assistant instance. If later seeking default HACS listing, follow HACS's current publication requirements and submit separately.

Updates: download the new HACS version (or replace the integration directory manually), restart Home Assistant, and review release notes. To roll back, restore the previous tagged directory/version and restart; do not replay prior power commands. Retain version-1 config compatibility unless a migration is implemented and tested.

For eventual Home Assistant core submission, keep only Home Assistant-specific code in the integration, retain the exact released library requirement, and adapt the custom-integration manifest fields and test locations to core conventions. The separate library is a prerequisite, not a substitute for hardware validation and the normal integration review/quality requirements.
