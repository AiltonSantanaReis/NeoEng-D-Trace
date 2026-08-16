@tool
class_name NeoEngDTraceManifestDiagnostic
extends RefCounted

const FORMAT_ID := "neoeng-d-trace-engine-integration"
const SCHEMA_VERSION := 1
const GENERATED_ROOT := "NeoEngGenerated"
const OVERRIDE_SUFFIX := ".ndt.override.json"
const SUPPORTED_ENGINE := "godot"


static func get_contract_info() -> Dictionary:
    return {
        "format_id": FORMAT_ID,
        "schema_version": SCHEMA_VERSION,
        "engine": SUPPORTED_ENGINE,
        "generated_root": GENERATED_ROOT,
        "override_suffix": OVERRIDE_SUFFIX,
        "destructive_update": false,
        "source_only": true,
    }


static func diagnose_manifest(manifest_path: String) -> Dictionary:
    var result := {
        "status": "FAILED",
        "manifest_path": manifest_path,
        "errors": [],
    }
    var errors: Array = result["errors"]
    if not _is_project_relative(manifest_path):
        errors.append("manifest path must use a res:// reference")
        return result
    if not FileAccess.file_exists(manifest_path):
        errors.append("manifest file does not exist")
        return result
    var handle := FileAccess.open(manifest_path, FileAccess.READ)
    if handle == null:
        errors.append("manifest file cannot be opened")
        return result
    var payload = JSON.parse_string(handle.get_as_text())
    if typeof(payload) != TYPE_DICTIONARY:
        errors.append("manifest JSON must be an object")
        return result
    _validate_payload(payload, errors)
    if errors.is_empty():
        result["status"] = "SUCCESS"
        result.erase("errors")
        result["format_id"] = FORMAT_ID
        result["schema_version"] = SCHEMA_VERSION
        result["engine"] = SUPPORTED_ENGINE
    return result


static func scan_project(root: String) -> Dictionary:
    var result := {
        "status": "SUCCESS",
        "root": root,
        "manifests": [],
        "errors": [],
    }
    if not _is_project_relative(root):
        result["status"] = "FAILED"
        result["errors"].append("scan root must use a res:// reference")
        return result
    if not DirAccess.dir_exists_absolute(root):
        return result
    var paths: Array[String] = []
    _collect_manifest_paths(root, paths)
    for path in paths:
        result["manifests"].append(diagnose_manifest(path))
    for manifest_result in result["manifests"]:
        if manifest_result.get("status") != "SUCCESS":
            result["status"] = "FAILED"
            result["errors"].append(manifest_result)
    return result


static func _collect_manifest_paths(root: String, paths: Array[String]) -> void:
    var files := DirAccess.get_files_at(root)
    for file_name in files:
        if file_name.ends_with(".ndt.integration.json"):
            paths.append(root.path_join(file_name))
    var directories := DirAccess.get_directories_at(root)
    for directory_name in directories:
        _collect_manifest_paths(root.path_join(directory_name), paths)


static func _validate_payload(payload: Dictionary, errors: Array) -> void:
    var expected_keys := ["format_id", "schema_version", "generator", "engine", "source", "sync", "metadata"]
    for key in expected_keys:
        if not payload.has(key):
            errors.append("missing manifest field: " + key)
    if not errors.is_empty():
        return
    if payload.get("format_id") != FORMAT_ID:
        errors.append("unsupported manifest format")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported manifest schema version")
    if payload.get("engine") != SUPPORTED_ENGINE:
        errors.append("manifest engine is not godot")
    var generator = payload.get("generator")
    if typeof(generator) != TYPE_DICTIONARY or generator.get("id") != "neoeng_d_trace" or not generator.has("version"):
        errors.append("manifest generator identity is invalid")
    var source = payload.get("source")
    if typeof(source) != TYPE_DICTIONARY or not source.has("image") or not source.has("metadata"):
        errors.append("manifest source is invalid")
    else:
        _validate_source(source, errors)
    var sync = payload.get("sync")
    if sync != {
        "direction": "dtrace-to-engine",
        "generated_root": GENERATED_ROOT,
        "override_suffix": OVERRIDE_SUFFIX,
        "destructive_update": false,
    }:
        errors.append("manifest sync policy is invalid")
    if typeof(payload.get("metadata")) != TYPE_DICTIONARY:
        errors.append("manifest metadata payload is invalid")


static func _validate_source(source: Dictionary, errors: Array) -> void:
    var image = source.get("image")
    var metadata = source.get("metadata")
    if typeof(image) != TYPE_DICTIONARY or not image.has("path") or not image.has("sha256"):
        errors.append("manifest image source is invalid")
    else:
        if not _is_safe_relative(image.get("path")):
            errors.append("manifest image path is not relative and safe")
        if typeof(image.get("sha256")) != TYPE_STRING or image.get("sha256").length() != 64:
            errors.append("manifest image hash is invalid")
    if typeof(metadata) != TYPE_DICTIONARY:
        errors.append("manifest metadata source is invalid")
    else:
        if typeof(metadata.get("sha256")) != TYPE_STRING or metadata.get("sha256").length() != 64:
            errors.append("manifest metadata hash is invalid")


static func _is_project_relative(path: String) -> bool:
    return typeof(path) == TYPE_STRING and path.begins_with("res://") and not path.contains("..")


static func _is_safe_relative(path: String) -> bool:
    if typeof(path) != TYPE_STRING or path.is_empty():
        return false
    var normalized := path.replace("\\", "/")
    if normalized.begins_with("/") or normalized.begins_with("//"):
        return false
    if normalized.length() >= 2 and normalized[1] == ":":
        return false
    for segment in normalized.split("/"):
        if segment == ".." or segment.is_empty():
            return false
    return true