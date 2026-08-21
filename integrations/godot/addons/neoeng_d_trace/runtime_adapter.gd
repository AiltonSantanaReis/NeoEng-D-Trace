@tool
class_name NeoEngDTraceRuntimeAdapter
extends RefCounted

const FORMAT_ID := "neoeng-d-trace-runtime-adapters"
const SCHEMA_VERSION := 1
const API_VERSION := 1
const CAPABILITIES := [
    "runtime.scene_loading",
    "runtime.lifecycle",
    "runtime.fixed_update",
    "runtime.lighting",
    "runtime.shaders",
    "runtime.particles",
    "runtime.post_processing",
    "runtime.triggers",
    "runtime.streaming",
]
const SIDECAR_CAPABILITIES := [
    "runtime.lighting",
    "runtime.shaders",
    "runtime.particles",
    "runtime.post_processing",
    "runtime.triggers",
    "runtime.streaming",
]


static func diagnose_bundle(bundle_path: String) -> Dictionary:
    var result := {"status": "FAILED", "errors": []}
    if not _is_project_relative(bundle_path) or not FileAccess.file_exists(bundle_path):
        result["errors"].append("runtime adapter bundle must be an existing res:// file")
        return result
    var raw := FileAccess.get_file_as_bytes(bundle_path)
    var payload = JSON.parse_string(raw.get_string_from_utf8())
    if typeof(payload) != TYPE_DICTIONARY:
        result["errors"].append("runtime adapter bundle JSON must be an object")
        return result
    _validate_bundle(payload, "res://", result["errors"])
    if result["errors"].is_empty():
        result["status"] = "SUCCESS"
        result.erase("errors")
    return result


static func import_bundle(bundle_path: String) -> Dictionary:
    var diagnostic := diagnose_bundle(bundle_path)
    if diagnostic.get("status") != "SUCCESS":
        return diagnostic
    var payload = JSON.parse_string(FileAccess.get_file_as_string(bundle_path))
    var root := Node2D.new()
    root.name = "NeoEngRuntimeScene"
    root.set_meta("neoeng_adapter_engine", "godot")
    root.set_meta("neoeng_adapter_bundle_sha256", _sha256_file(bundle_path))
    root.set_meta("neoeng_scenario_hash", str(payload["source"]["sha256"]))
    root.set_meta("neoeng_fixed_tick", 0)
    root.set_meta("neoeng_simulation_time", 0.0)
    root.set_meta("neoeng_capabilities", payload["capabilities"]["godot"]["support"])
    var scenario_path := "res://".path_join(str(payload["source"]["path"]))
    var scenario = JSON.parse_string(FileAccess.get_file_as_string(scenario_path))
    root.set_meta("neoeng_camera_position", Vector2(
        float(scenario["camera"]["position"]["x"]),
        float(scenario["camera"]["position"]["y"]),
    ))
    root.set_meta("neoeng_camera_zoom", float(scenario["camera"]["zoom"]))
    for index in scenario["layers"].size():
        var layer_data: Dictionary = scenario["layers"][index]
        var layer := Node2D.new()
        layer.name = "Layer_%d" % index
        layer.visible = bool(layer_data["visible"])
        layer.set_meta("neoeng_layer_id", str(layer_data["id"]))
        layer.set_meta("neoeng_layer_name", str(layer_data["name"]))
        layer.set_meta("neoeng_object_ids", PackedStringArray(layer_data["object_ids"]))
        layer.set_meta("neoeng_parallax", layer_data["parallax"])
        root.add_child(layer)
    return {"status": "SUCCESS", "root": root, "payload": payload}


static func advance_fixed_ticks(root: Node, ticks: int, fixed_dt: float = 1.0 / 60.0) -> bool:
    if root == null or ticks < 0 or not is_finite(fixed_dt) or fixed_dt <= 0.0:
        return false
    var current_tick := int(root.get_meta("neoeng_fixed_tick", 0))
    var current_time := float(root.get_meta("neoeng_simulation_time", 0.0))
    root.set_meta("neoeng_fixed_tick", current_tick + ticks)
    root.set_meta("neoeng_simulation_time", current_time + float(ticks) * fixed_dt)
    return true


static func _validate_bundle(payload: Dictionary, base_dir: String, errors: Array) -> void:
    if not _exact_keys(payload, ["format_id", "schema_version", "api_version", "generator", "source", "sidecars", "capabilities"]):
        errors.append("runtime adapter bundle keys are invalid")
        return
    if payload["format_id"] != FORMAT_ID or payload["schema_version"] != SCHEMA_VERSION or payload["api_version"] != API_VERSION:
        errors.append("unsupported runtime adapter bundle version")
    if not _exact_keys(payload["generator"], ["id", "version"]) or payload["generator"]["id"] != "neoeng_d_trace":
        errors.append("runtime adapter generator is invalid")
    _validate_file_binding(payload["source"], base_dir, "source", errors)
    var sidecars: Variant = payload["sidecars"]
    if typeof(sidecars) != TYPE_ARRAY or sidecars.size() != SIDECAR_CAPABILITIES.size():
        errors.append("runtime adapter sidecars are incomplete")
    else:
        var seen := {}
        for sidecar_value in sidecars:
            var sidecar: Variant = sidecar_value
            if not _exact_keys(sidecar, ["capability", "path", "format_id", "schema_version", "sha256", "bytes", "required"]):
                errors.append("runtime adapter sidecar record is invalid")
                continue
            if not SIDECAR_CAPABILITIES.has(sidecar["capability"]) or seen.has(sidecar["capability"]):
                errors.append("runtime adapter sidecar capability is duplicated or unknown")
            seen[sidecar["capability"]] = true
            _validate_file_binding(sidecar, base_dir, "sidecar", errors)
            if sidecar["required"] != true:
                errors.append("runtime adapter sidecars must be required")
    if not _validate_matrix(payload["capabilities"], errors):
        return


static func _validate_file_binding(binding: Variant, base_dir: String, label: String, errors: Array) -> void:
    if typeof(binding) != TYPE_DICTIONARY or not binding.has("path") or not binding.has("sha256") or not binding.has("bytes"):
        errors.append(label + " file binding is incomplete")
        return
    var relative := str(binding["path"])
    if not _safe_relative_path(relative):
        errors.append(label + " path is unsafe")
        return
    var path := base_dir.path_join(relative)
    if not FileAccess.file_exists(path):
        errors.append(label + " file does not exist")
        return
    var bytes := FileAccess.get_file_as_bytes(path)
    if int(binding["bytes"]) != bytes.size() or str(binding["sha256"]) != _sha256_bytes(bytes):
        errors.append(label + " file hash or size mismatch")


static func _validate_matrix(value: Variant, errors: Array) -> bool:
    if typeof(value) != TYPE_DICTIONARY or not value.has("godot") or not value.has("unity"):
        errors.append("runtime adapter capability matrix is incomplete")
        return false
    for engine in ["godot", "unity"]:
        var entry: Variant = value[engine]
        if not _exact_keys(entry, ["adapter_id", "adapter_version", "support"]):
            errors.append(engine + " adapter matrix entry is invalid")
            continue
        if int(entry["adapter_version"]) != 1:
            errors.append(engine + " adapter version is unsupported")
        var support: Variant = entry["support"]
        if typeof(support) != TYPE_ARRAY or support.size() != CAPABILITIES.size():
            errors.append(engine + " adapter support matrix is incomplete")
            continue
        var seen := {}
        for decision_value in support:
            var decision: Variant = decision_value
            if not _exact_keys(decision, ["id", "compatibility", "mode", "reason"]):
                errors.append(engine + " capability decision is invalid")
                continue
            if not CAPABILITIES.has(decision["id"]) or seen.has(decision["id"]):
                errors.append(engine + " capability decision id is invalid")
            seen[decision["id"]] = true
        if seen.size() != CAPABILITIES.size():
            errors.append(engine + " capability support matrix is incomplete")
    return errors.is_empty()

static func _exact_keys(value: Variant, expected: Array) -> bool:
    if typeof(value) != TYPE_DICTIONARY:
        return false
    var dictionary: Dictionary = value
    if dictionary.size() != expected.size():
        return false
    for key in expected:
        if not dictionary.has(key):
            return false
    return true


static func _safe_relative_path(path: String) -> bool:
    return not path.is_empty() and not path.begins_with("/") and not path.contains("..") and not path.contains("\\") and not path.contains(":")


static func _is_project_relative(path: String) -> bool:
    return path.begins_with("res://") and not path.contains("..")


static func _sha256_file(path: String) -> String:
    return _sha256_bytes(FileAccess.get_file_as_bytes(path))


static func _sha256_bytes(bytes: PackedByteArray) -> String:
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    context.update(bytes)
    return context.finish().hex_encode()
