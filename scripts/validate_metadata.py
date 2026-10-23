"""Validate local packaging and translation contracts without publishing to GitHub."""

import ast
import json
import tomllib
from importlib.metadata import version
from pathlib import Path

import yaml
from mygrid_modbus import FAULTS

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
    assert manifest["dependencies"] == ["modbus"]
    assert manifest["loggers"] == ["modbus_connection", "tmodbus"]
    assert manifest["requirements"] == ["mygrid-modbus==0.1.0"]
    assert project["project"]["dependencies"] == manifest["requirements"]
    assert version("mygrid-modbus") == "0.1.0"
    assert not (COMPONENT / "client.py").exists(), "Protocol belongs in the library"
    for path in COMPONENT.glob("*.py"):
        tree = ast.parse(path.read_text())
        assert not any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any(
                name == "pymodbus"
                or name.startswith("pymodbus.")
                or name == "tmodbus"
                or name.startswith("tmodbus.")
                or name.startswith("modbus_connection.tmodbus")
                or name.startswith("modbus_connection.pymodbus")
                for name in (
                    [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else [item.name for item in node.names]
                )
            )
            for node in ast.walk(tree)
        ), f"Direct transport import in {path.name}"
    assert "quality_scale" not in manifest, "Custom integration has no official rating"
    assert hacs["homeassistant"] == "2026.10.2"
    strings = json.loads((COMPONENT / "strings.json").read_text())
    assert json.loads((COMPONENT / "translations" / "en.json").read_text()) == strings
    faults = FAULTS
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
