"""Generate the HACS integration from the core overlay and the standalone libraries."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = Path("custom_components/mygrid")
LIBRARIES = {
    # distribution name -> (package directory name, default checkout beside this repo)
    "mygrid-modbus": ("mygrid_modbus", "mygrid-modbus"),
    "mygrid-voltbridge": ("mygrid_voltbridge", "mygrid-voltbridge"),
}


def revision(path: Path) -> str:
    """Record provenance without requiring a remote repository."""
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def format_python(content: str, path: Path) -> str:
    """Normalize import groups after namespace adaptation, using project tools."""
    result = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            "I",
            "--fix",
            # Classify imports the same way no matter which files already exist.
            "--config",
            "lint.isort.known-first-party = ['custom_components', 'tests']",
            "--stdin-filename",
            str(path),
            "-",
        ],
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


def adapt_imports(content: str, prefix: str) -> str:
    """Point absolute library imports at the vendored copies."""
    for _, (package, _) in LIBRARIES.items():
        content = content.replace(
            f"from {package} import", f"from {prefix}.vendor.{package} import"
        )
    return content


def required_versions(manifest: dict[str, object]) -> dict[str, str]:
    """Read the pinned library versions from the core manifest's requirements."""
    pins = {}
    for requirement in manifest["requirements"]:  # type: ignore[attr-defined]
        match = re.fullmatch(r"([a-z-]+)==([0-9][^\s]*)", str(requirement))
        assert match, f"Unpinned requirement: {requirement}"
        pins[match.group(1)] = match.group(2)
    assert set(pins) == set(LIBRARIES), (
        "Core requirements differ from vendored libraries"
    )
    return pins


def expected(core: Path, libraries: dict[str, Path]) -> dict[Path, bytes]:
    """Adapt namespaces only; the device libraries are copied byte for byte."""
    files: dict[Path, bytes] = {}
    integration_version = json.loads(
        (ROOT / "custom_components/mygrid/manifest.json").read_text()
    )["version"]
    source = core / "homeassistant/components/mygrid"
    pins = required_versions(json.loads((source / "manifest.json").read_text()))
    for path in sorted(source.iterdir()):
        if path.suffix not in (".py", ".json", ".yaml"):
            continue
        content = path.read_text()
        if path.suffix == ".py":
            content = adapt_imports(content, "")
        if path.name == "manifest.json":
            data = json.loads(content)
            data.update(
                version=integration_version,
                documentation="https://github.com/tjorim/ha-mygrid/blob/main/README.md",
                issue_tracker="https://github.com/tjorim/ha-mygrid/issues",
                requirements=[],
            )
            keys = ["domain", "name", *sorted(set(data) - {"domain", "name"})]
            content = json.dumps({key: data[key] for key in keys}, indent=2) + "\n"
        files[COMPONENT / path.name] = (
            format_python(content, COMPONENT / path.name)
            if path.suffix == ".py"
            else content
        ).encode()
    files[COMPONENT / "translations/en.json"] = (source / "strings.json").read_bytes()
    vendor = COMPONENT / "vendor"
    files[vendor / "__init__.py"] = (
        b'"""Generated dependencies; update with scripts/sync_sources.py."""\n'
    )
    provenance_libraries = {}
    for name, (package, _) in LIBRARIES.items():
        library = libraries[name]
        hashes = {}
        for path in sorted((library / "src" / package).iterdir()):
            if path.suffix == ".py" or path.name == "py.typed":
                content = path.read_bytes()
                files[vendor / package / path.name] = content
                hashes[path.name] = hashlib.sha256(content).hexdigest()
        files[vendor / f"LICENSE.{name}"] = (library / "LICENSE").read_bytes()
        provenance_libraries[name] = {
            "version": pins[name],
            "commit": revision(library),
            "sha256": hashes,
        }
    provenance = {
        "libraries": provenance_libraries,
        "core_commit": revision(core),
        "adapter_sha256": {
            str(path.relative_to(COMPONENT)): hashlib.sha256(content).hexdigest()
            for path, content in files.items()
            if path.parts[:2] == ("custom_components", "mygrid")
            and "vendor" not in path.parts
        },
    }
    files[vendor / "origin.json"] = (
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    ).encode()
    tests = core / "tests/components/mygrid"
    for path in sorted(tests.iterdir()):
        if path.is_dir():
            if path.name != "fixtures":
                continue
            for fixture in sorted(path.iterdir()):
                files[Path("tests") / path.name / fixture.name] = fixture.read_bytes()
            continue
        if path.suffix != ".py":
            continue
        content = adapt_imports(
            path.read_text().replace(
                "homeassistant.components.mygrid", "custom_components.mygrid"
            ),
            "custom_components.mygrid",
        )
        content = content.replace(
            "from tests.common import",
            "from pytest_homeassistant_custom_component.common import",
        ).replace("tests.components.mygrid.", "tests.")
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
    for name, (_, directory) in LIBRARIES.items():
        parser.add_argument(
            f"--{directory}", type=Path, default=ROOT.parent / directory, dest=name
        )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = expected(args.core, {name: getattr(args, name) for name in LIBRARIES})
    different = [
        str(path)
        for path, data in files.items()
        if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
    ]
    stale = [
        path
        for pattern in (
            "custom_components/mygrid/*.py",
            "custom_components/mygrid/vendor/*/*.py",
            "tests/*.py",
        )
        for path in ROOT.glob(pattern)
        if path.relative_to(ROOT) not in files
    ]
    different.extend(str(path.relative_to(ROOT)) for path in stale)
    if args.check:
        if different:
            raise SystemExit("Generated files differ: " + ", ".join(different))
        print("Core adapter and vendored libraries match their canonical sources.")
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
