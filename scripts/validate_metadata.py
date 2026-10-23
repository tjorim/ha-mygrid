"""Validate the standalone HACS package and its generated library provenance."""

import ast
import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/mygrid"
LIBRARIES = {"mygrid-modbus": "mygrid_modbus", "mygrid-voltbridge": "mygrid_voltbridge"}
FORBIDDEN_IMPORTS = (
    "pymodbus",
    "tmodbus",
    "mygrid_modbus",
    "mygrid_voltbridge",
    "modbus_connection.tmodbus",
    "modbus_connection.pymodbus",
)


def main() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert list(manifest) == [
        "domain",
        "name",
        *sorted(set(manifest) - {"domain", "name"}),
    ]
    assert manifest["domain"] == "mygrid"
    assert manifest["version"] == project["project"]["version"] == "0.1.0"
    assert manifest["requirements"] == project["project"]["dependencies"] == []
    assert manifest["dependencies"] == ["modbus"]
    assert manifest["dhcp"] == [{"registered_devices": True}]
    assert manifest["zeroconf"] == [
        {"type": "_mygrid._tcp.local.", "properties": {"model": "voltbridge*"}}
    ]
    assert manifest["config_flow"] and manifest["iot_class"] == "local_polling"
    assert "quality_scale" not in manifest
    assert json.loads((COMPONENT / "strings.json").read_text()) == json.loads(
        (COMPONENT / "translations/en.json").read_text()
    )
    vendor = COMPONENT / "vendor"
    origin = json.loads((vendor / "origin.json").read_text())
    assert set(origin["libraries"]) == set(LIBRARIES)
    for name, package in LIBRARIES.items():
        recorded = origin["libraries"][name]
        actual = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (vendor / package).iterdir()
            if path.suffix == ".py" or path.name == "py.typed"
        }
        assert actual == recorded["sha256"], (
            f"Vendored {name} differs from recorded source hashes"
        )
        assert (vendor / f"LICENSE.{name}").exists()
    adapter_files = (
        list(COMPONENT.glob("*.py"))
        + list(COMPONENT.glob("*.json"))
        + list(COMPONENT.glob("*.yaml"))
        + [COMPONENT / "translations/en.json"]
    )
    adapter = {
        str(path.relative_to(COMPONENT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in adapter_files
    }
    assert adapter == origin["adapter_sha256"], (
        "Generated adapter differs from canonical-source hashes"
    )
    for path in COMPONENT.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith(FORBIDDEN_IMPORTS), path
    print(
        "HACS metadata, offline vendoring provenance, and namespace boundaries validated."
    )


if __name__ == "__main__":
    main()
