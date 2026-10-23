# Releasing

This delivery creates a local Git repository only. HACS installation from a custom repository becomes possible after a maintainer publishes it on GitHub.

1. Confirm the GitHub owner/repository and maintainer. Manifest links and `codeowners` are prepared for `tjorim/ha-mygrid`, based on the connected GitHub account; these links will become live only if the local repository is published there. If publishing elsewhere, update `documentation`, `issue_tracker` and `codeowners` first. No remote repository was created.
2. Add a GitHub repository description and suitable `home-assistant`, `hacs`, `mygrid`, and `modbus` topics. Keep the repository layout as shipped: `custom_components/mygrid`.
3. Run the locked development commands in README. CI enforces lint, formatting, strict types, at least 95% branch-aware coverage, local metadata validation and HACS validation. HACS's remote action needs a real GitHub repository and cannot be fully verified locally.
4. Complete and record the hardware checklist; document any firmware or cluster limitations. Do not label the release physically verified until results exist.
5. Review every `quality_scale.yaml` entry and evidence, especially the unresolved maintainer/branding items. Official Platinum grading is unavailable to a standalone custom integration; do not set a misleading manifest rating.
6. Keep `manifest.json` and `pyproject.toml` versions aligned. Tag `v0.1.0`, create GitHub release notes describing compatibility and known limitations, and publish the repository.
7. Test HACS custom-repository installation in a clean Home Assistant instance. If later seeking default HACS listing, follow HACS's current publication requirements and submit separately.

Updates: download the new HACS version (or replace the integration directory manually), restart Home Assistant, and review release notes. To roll back, restore the previous tagged directory/version and restart; do not replay prior power commands. Retain version-1 config compatibility unless a migration is implemented and tested.
