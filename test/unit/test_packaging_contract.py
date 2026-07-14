"""Source and wheel checks for the Components V2 release contract."""

from email.parser import BytesParser
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tomllib
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import pytest


ROOT = Path(__file__).resolve().parents[2]


def _normalized_name(value):
    return re.sub(r"[-_.]+", "-", value).lower()


def _normalized_version(value):
    # Poetry accepts the dotted prerelease spelling while wheel metadata uses
    # its canonical PEP 440 representation.
    return value.replace(".rc", "rc")


def _manifest(pyproject):
    components = pyproject["tool"]["streamlit"]["component"]["components"]
    assert len(components) == 1
    return components[0]


def _candidate_wheel():
    configured = os.environ.get("STREAMLIT_AGGRID_WHEEL")
    if configured:
        return Path(configured)

    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if len(wheels) > 1:
        raise AssertionError(
            "multiple wheels found in dist; validate and publish one exact artifact: "
            + ", ".join(str(path) for path in wheels)
        )
    if len(wheels) == 1:
        return wheels[0]
    return None


def test_source_metadata_and_component_manifest_are_consistent():
    root = tomllib.loads((ROOT / "pyproject.toml").read_text())
    embedded = tomllib.loads(
        (ROOT / "streamlit_aggrid" / "pyproject.toml").read_text()
    )

    assert _normalized_name(root["project"]["name"]) == "streamlit-aggrid"
    assert _normalized_name(embedded["project"]["name"]) == "streamlit-aggrid"
    assert _normalized_version(root["project"]["version"]) == _normalized_version(
        embedded["project"]["version"]
    )
    assert {entry["include"] for entry in root["tool"]["poetry"]["packages"]} == {
        "st_aggrid",
        "streamlit_aggrid",
    }

    manifest = _manifest(embedded)
    assert manifest["name"] == "agGrid"
    assert manifest["asset_dir"] == "frontend/build"


def test_built_wheel_contains_matching_metadata_manifest_and_assets(tmp_path):
    wheel = _candidate_wheel()
    if wheel is None:
        pytest.skip(
            "build a wheel or set STREAMLIT_AGGRID_WHEEL to validate the release artifact"
        )
    assert wheel.is_file(), f"wheel does not exist: {wheel}"

    root = tomllib.loads((ROOT / "pyproject.toml").read_text())
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        assert len(metadata_names) == 1
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))

        assert _normalized_name(metadata["Name"]) == _normalized_name(
            root["project"]["name"]
        )
        assert _normalized_version(metadata["Version"]) == _normalized_version(
            root["project"]["version"]
        )

        source_requirements = {
            canonicalize_name(requirement.name): requirement
            for value in root["project"]["dependencies"]
            if (requirement := Requirement(value))
        }
        wheel_requirements = {
            canonicalize_name(requirement.name): requirement
            for value in metadata.get_all("Requires-Dist", [])
            if (requirement := Requirement(value))
        }
        for name, source_requirement in source_requirements.items():
            assert name in wheel_requirements
            assert (
                wheel_requirements[name].specifier == source_requirement.specifier
            ), f"wheel has stale dependency metadata for {name}"

        assert "st_aggrid/__init__.py" in names
        assert "streamlit_aggrid/__init__.py" in names

        embedded_path = "streamlit_aggrid/pyproject.toml"
        assert embedded_path in names
        embedded = tomllib.loads(archive.read(embedded_path).decode())
        manifest = _manifest(embedded)
        asset_prefix = PurePosixPath("streamlit_aggrid") / manifest["asset_dir"]
        asset_prefix = f"{asset_prefix.as_posix()}/"

        assets = [name for name in names if name.startswith(asset_prefix)]
        assert any(name.endswith(".mjs") for name in assets)
        assert any(name.endswith(".css") for name in assets)

        extracted = tmp_path / "wheel"
        archive.extractall(extracted)

    # ZIP membership alone is insufficient: rc1 contained an asset_dir that
    # looked plausible but resolved outside the implementation package when
    # Streamlit scanned the installed distribution. Exercise the same manager
    # and definition validation path Streamlit uses at runtime.
    smoke_test = r"""
import importlib
from pathlib import Path
import sys

wheel_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(wheel_root))

st_aggrid = importlib.import_module("st_aggrid")
streamlit_aggrid = importlib.import_module("streamlit_aggrid")
assert st_aggrid.AgGrid is streamlit_aggrid.AgGrid
for submodule in (
    "AgGrid",
    "AgGridReturn",
    "aggrid_utils",
    "grid_options_builder",
    "shared",
    "styles",
):
    legacy = importlib.import_module(f"st_aggrid.{submodule}")
    implementation = importlib.import_module(f"streamlit_aggrid.{submodule}")
    assert legacy is implementation

from streamlit.components.v2.component_manager import BidiComponentManager

manager = BidiComponentManager()
manager.discover_and_register_components(start_file_watching=False)
component_key = "streamlit-aggrid.agGrid"
definition = manager.get(component_key)
assert definition is not None, f"manifest did not register {component_key}"

asset_root = manager.get_component_asset_root(component_key)
assert asset_root is not None and asset_root.is_dir(), asset_root
assert wheel_root in asset_root.resolve().parents

validated = manager.build_definition_with_validation(
    component_key=component_key,
    html=None,
    css="index-*.css",
    js="index-*.mjs",
)
assert validated is not None
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", smoke_test, str(extracted)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, (
        "wheel failed isolated import/component-manifest smoke test\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
