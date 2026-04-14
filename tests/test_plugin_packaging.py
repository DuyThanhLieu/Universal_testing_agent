from pathlib import Path

from orchestrator.plugin_packaging import export_plugin_package, import_plugin_package
from orchestrator.registry import get_registry


def test_export_plugin_package_writes_metadata_file(tmp_path: Path) -> None:
    registry = get_registry(force_reload=True)
    package_path, payload = export_plugin_package(registry, "web", tmp_path)
    assert package_path.exists()
    assert payload["plugin_name"] == "web"
    assert payload["plugin_version"] == "1.8.0"
    assert payload["author"]


def test_import_plugin_package_persists_import_record(tmp_path: Path) -> None:
    registry = get_registry(force_reload=True)
    package_path, _ = export_plugin_package(registry, "api", tmp_path / "exports")
    imported_path, payload, errors = import_plugin_package(package_path, tmp_path / "imports")
    assert imported_path.exists()
    assert payload["plugin_name"] == "api"
    assert errors == []
