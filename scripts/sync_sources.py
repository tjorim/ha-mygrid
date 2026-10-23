"""Generate the HACS integration from the core overlay and standalone library."""

import argparse
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def revision(path: Path) -> str:
    """Record provenance without requiring a remote repository."""
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def format_python(content: str, path: Path) -> str:
    """Normalize import groups after namespace adaptation, using project tools."""
    result = subprocess.run(
        ["ruff", "check", "--select", "I", "--fix", "--stdin-filename", str(path), "-"],
        input=content,
        text=True,
        capture_output=True,
        check=True,
    )
    return subprocess.run(
        ["ruff", "format", "--stdin-filename", str(path), "-"],
        input=result.stdout,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def expected(core: Path, library: Path) -> dict[Path, bytes]:
    """Adapt namespaces only; the device model is copied byte for byte."""
    files: dict[Path, bytes] = {}
    library_version = tomllib.loads((library / "pyproject.toml").read_text())[
        "project"
    ]["version"]
    integration_version = tomllib.loads((ROOT / "pyproject.toml").read_text())[
        "project"
    ]["version"]
    source = core / "homeassistant/components/mygrid"
    for path in source.iterdir():
        if path.suffix not in (".py", ".json", ".yaml"):
            continue
        content = path.read_text()
        if path.suffix == ".py":
            content = content.replace(
                "from mygrid_modbus import", "from .vendor.mygrid_modbus import"
            )
        if path.name == "manifest.json":
            data = json.loads(content)
            assert data["requirements"] == [f"mygrid-modbus=={library_version}"], (
                "Core and library versions differ"
            )
            data.update(
                version=integration_version,
                documentation="https://github.com/tjorim/ha-mygrid/blob/main/README.md",
                issue_tracker="https://github.com/tjorim/ha-mygrid/issues",
                requirements=[],
            )
            content = json.dumps(dict(sorted(data.items())), indent=2) + "\n"
        files[Path("custom_components/mygrid") / path.name] = (
            format_python(content, Path("custom_components/mygrid") / path.name)
            if path.suffix == ".py"
            else content
        ).encode()
    files[Path("custom_components/mygrid/translations/en.json")] = (
        source / "strings.json"
    ).read_bytes()
    vendor = Path("custom_components/mygrid/vendor")
    files[vendor / "__init__.py"] = (
        b'"""Generated dependencies; update with scripts/sync_sources.py."""\n'
    )
    hashes = {}
    for path in sorted((library / "src/mygrid_modbus").iterdir()):
        if path.suffix == ".py" or path.name == "py.typed":
            content = path.read_bytes()
            files[vendor / "mygrid_modbus" / path.name] = content
            hashes[path.name] = hashlib.sha256(content).hexdigest()
    files[vendor / "LICENSE.mygrid-modbus"] = (library / "LICENSE").read_bytes()
    provenance = {
        "library": "mygrid-modbus",
        "version": library_version,
        "library_commit": revision(library),
        "core_commit": revision(core),
        "sha256": hashes,
        "adapter_sha256": {
            str(path.relative_to("custom_components/mygrid")): hashlib.sha256(
                content
            ).hexdigest()
            for path, content in files.items()
            if path.parts[:2] == ("custom_components", "mygrid")
            and "vendor" not in path.parts
        },
    }
    files[vendor / "origin.json"] = (
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    ).encode()
    for path in (core / "tests/components/mygrid").glob("*.py"):
        content = (
            path.read_text()
            .replace("homeassistant.components.mygrid", "custom_components.mygrid")
            .replace(
                "from mygrid_modbus import",
                "from custom_components.mygrid.vendor.mygrid_modbus import",
            )
            .replace(
                "from tests.common import",
                "from pytest_homeassistant_custom_component.common import",
            )
            .replace(
                "from tests.components.mygrid.simulator import",
                "from tests.simulator import",
            )
        )
        if path.name == "conftest.py":
            content += '\n\n@pytest.fixture(autouse=True)\ndef custom_integrations(enable_custom_integrations):\n    """Enable the generated custom integration in the test runtime."""\n'
        files[Path("tests") / path.name] = format_python(
            content, Path("tests") / path.name
        ).encode()
    return files


def main() -> None:
    """Write sources, or verify that none have drifted from their originals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, default=ROOT.parent / "ha-mygrid-core")
    parser.add_argument("--library", type=Path, default=ROOT.parent / "mygrid-modbus")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = expected(args.core, args.library)
    different = [
        str(path)
        for path, data in files.items()
        if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
    ]
    vendor_path = ROOT / "custom_components/mygrid/vendor/mygrid_modbus"
    stale = [
        path for path in vendor_path.glob("*.py") if path.relative_to(ROOT) not in files
    ]
    different.extend(str(path.relative_to(ROOT)) for path in stale)
    if args.check:
        if different:
            raise SystemExit("Generated files differ: " + ", ".join(different))
        print("Core adapter and vendored library match their canonical sources.")
        return
    for path in stale:
        path.unlink()
    for path, data in files.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"Generated {len(files)} files from the core and library sources.")


if __name__ == "__main__":
    main()
