"""Validate local packaging and translation contracts without publishing to GitHub."""

import ast
import json
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mygrid"


def main() -> None:
    """Fail CI for mismatched versions, missing names or stale quality entries."""
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert manifest["domain"] == "mygrid"
    assert manifest["codeowners"] == ["@tjorim"]
    assert manifest["documentation"].startswith("https://github.com/tjorim/ha-mygrid/")
    assert manifest["issue_tracker"].startswith("https://github.com/tjorim/ha-mygrid/")
    assert manifest["version"] == project["project"]["version"]
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "local_polling"
    assert manifest["requirements"] == ["pymodbus==3.13.1"]
    assert "quality_scale" not in manifest, "Custom integration has no official rating"
    assert hacs["homeassistant"] == "2026.10.2"
    strings = json.loads((COMPONENT / "strings.json").read_text())
    assert json.loads((COMPONENT / "translations" / "en.json").read_text()) == strings
    parsed = ast.parse((COMPONENT / "client.py").read_text())
    faults = next(
        ast.literal_eval(node.value)
        for node in parsed.body
        if isinstance(node, ast.AnnAssign)
        and getattr(node.target, "id", None) == "FAULTS"
    )
    assert len(faults) == 22
    assert all(
        f"fault_{name}" in strings["entity"]["binary_sensor"]
        for name in faults.values()
    )
    for filename in ["manifest.json", "strings.json", "icons.json"]:
        json.loads((COMPONENT / filename).read_text())
    rules = yaml.safe_load((COMPONENT / "quality_scale.yaml").read_text())["rules"]
    assert len(rules) >= 50
    for key, rule in rules.items():
        assert rule["status"] in {"done", "todo", "exempt"}, key
        assert rule["comment"], key
    for section in strings["entity"].values():
        assert all(entity.get("name") for entity in section.values())
    print("Metadata, versions, translations and quality tracking validated.")


if __name__ == "__main__":
    main()
