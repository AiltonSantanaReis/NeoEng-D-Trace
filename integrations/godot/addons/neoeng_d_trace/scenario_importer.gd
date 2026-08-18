@tool
class_name NeoEngDTraceScenarioImporter
extends RefCounted

const FORMAT_ID := "neoeng-d-trace-scenario-runtime"
const SCHEMA_VERSION := 1


static func diagnose_export(export_path: String) -> Dictionary:
    var result := {"status": "FAILED", "errors": []}
    if not _is_project_relative(export_path) or not FileAccess.file_exists(export_path):
        result["errors"].append("scenario export path must be an existing res:// file")
        return result
    var handle := FileAccess.open(export_path, FileAccess.READ)
    if handle == null:
        result["errors"].append("scenario export cannot be opened")
        return result
    var payload = JSON.parse_string(handle.get_as_text())
    if typeof(payload) != TYPE_DICTIONARY:
        result["errors"].append("scenario export JSON must be an object")
        return result
    _validate_payload(payload, result["errors"])
    if result["errors"].is_empty():
        result["status"] = "SUCCESS"
        result.erase("errors")
    return result


static func import_scenario(export_path: String) -> Dictionary:
    var diagnostic := diagnose_export(export_path)
    if diagnostic.get("status") != "SUCCESS":
        return diagnostic
    var handle := FileAccess.open(export_path, FileAccess.READ)
    var payload = JSON.parse_string(handle.get_as_text())
    var root := Node2D.new()
    root.name = "NeoEngScenario"
    root.set_meta("neoeng_scenario_hash", str(payload["source"]["sha256"]))
    root.set_meta("neoeng_project_hash", str(payload["project"]["sha256"]))
    root.set_meta("neoeng_camera_position", Vector2(
        float(payload["camera"]["position"]["x"]),
        float(payload["camera"]["position"]["y"]),
    ))
    root.set_meta("neoeng_camera_zoom", float(payload["camera"]["zoom"]))
    for index in payload["layers"].size():
        var layer_data: Dictionary = payload["layers"][index]
        var layer := Node2D.new()
        layer.name = "Layer_%d" % index
        layer.visible = bool(layer_data["visible"])
        layer.set_meta("neoeng_layer_id", str(layer_data["id"]))
        layer.set_meta("neoeng_layer_name", str(layer_data["name"]))
        layer.set_meta("neoeng_object_ids", PackedStringArray(layer_data["object_ids"]))
        layer.set_meta("neoeng_parallax_depth", float(layer_data["parallax"]["depth"]))
        layer.set_meta("neoeng_parallax_translation_strength", float(layer_data["parallax"]["translation_strength"]))
        layer.set_meta("neoeng_parallax_zoom_strength", float(layer_data["parallax"]["zoom_strength"]))
        root.add_child(layer)
    return {"status": "SUCCESS", "root": root, "payload": payload}


static func _validate_payload(payload: Dictionary, errors: Array) -> void:
    var expected_keys := ["format_id", "schema_version", "generator", "source", "project", "camera", "layers"]
    for key in expected_keys:
        if not payload.has(key):
            errors.append("scenario export is missing " + key)
    if not errors.is_empty():
        return
    if payload["format_id"] != FORMAT_ID or payload["schema_version"] != SCHEMA_VERSION:
        errors.append("unsupported scenario export format or version")
    var generator = payload["generator"]
    if typeof(generator) != TYPE_DICTIONARY or typeof(generator.get("id")) != TYPE_STRING or typeof(generator.get("version")) != TYPE_STRING:
        errors.append("scenario export generator is invalid")
    for section_name in ["source", "project"]:
        var binding = payload[section_name]
        if typeof(binding) != TYPE_DICTIONARY or typeof(binding.get("sha256")) != TYPE_STRING or str(binding.get("sha256")).length() != 64:
            errors.append("scenario export " + section_name + " binding is invalid")
    var camera = payload["camera"]
    if typeof(camera) != TYPE_DICTIONARY or typeof(camera.get("position")) != TYPE_DICTIONARY or not _finite(camera.get("zoom")) or float(camera.get("zoom")) <= 0.0:
        errors.append("scenario export camera is invalid")
    var layers = payload["layers"]
    if typeof(layers) != TYPE_ARRAY:
        errors.append("scenario export layers are invalid")
        return
    var ids := {}
    for layer in layers:
        if typeof(layer) != TYPE_DICTIONARY or not layer.has("id") or ids.has(str(layer.get("id"))):
            errors.append("scenario export layer IDs are invalid or duplicated")
            continue
        ids[str(layer["id"])] = true
        if typeof(layer.get("object_ids")) != TYPE_ARRAY or typeof(layer.get("parallax")) != TYPE_DICTIONARY:
            errors.append("scenario export layer payload is invalid")


static func _finite(value: Variant) -> bool:
    return (typeof(value) == TYPE_FLOAT or typeof(value) == TYPE_INT) and is_finite(float(value))


static func _is_project_relative(path: String) -> bool:
    return path.begins_with("res://") and not path.contains("..")
