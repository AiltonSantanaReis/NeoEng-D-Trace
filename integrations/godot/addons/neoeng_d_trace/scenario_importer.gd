@tool
class_name NeoEngDTraceScenarioImporter
extends RefCounted

const FORMAT_ID := "neoeng-d-trace-scenario-runtime"
const SCENARIO_FORMAT_ID := "neoeng-d-trace-scenario"
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
    if not _exact_keys(payload, ["format_id", "schema_version", "generator", "source", "project", "camera", "layers"]):
        errors.append("scenario export keys are invalid")
        return
    if payload["format_id"] != FORMAT_ID or payload["schema_version"] != SCHEMA_VERSION:
        errors.append("unsupported scenario export format or version")
    var generator: Variant = payload["generator"]
    if not _exact_keys(generator, ["id", "version"]) or generator["id"] != "neoeng_d_trace" or typeof(generator["version"]) != TYPE_STRING or String(generator["version"]).is_empty():
        errors.append("scenario export generator is invalid")
    for section_name in ["source", "project"]:
        var binding: Variant = payload[section_name]
        var expected_format := SCENARIO_FORMAT_ID if section_name == "source" else "neoeng-d-trace-project"
        if not _exact_keys(binding, ["format_id", "schema_version", "sha256"]) or binding["format_id"] != expected_format or binding["schema_version"] != 1 or not _lower_hex_hash(binding["sha256"]):
            errors.append("scenario export " + section_name + " binding is invalid")
    var camera: Variant = payload["camera"]
    var position: Variant = camera["position"] if _exact_keys(camera, ["position", "zoom"]) else null
    if not _exact_keys(camera, ["position", "zoom"]) or not _exact_keys(position, ["x", "y"]) or not _finite(position["x"]) or not _finite(position["y"]) or not _finite(camera["zoom"]) or float(camera["zoom"]) <= 0.0:
        errors.append("scenario export camera is invalid")
    var layers: Variant = payload["layers"]
    if typeof(layers) != TYPE_ARRAY or layers.size() > 256:
        errors.append("scenario export layers are invalid")
        return
    var layer_ids := {}
    var object_ids := {}
    var object_reference_count := 0
    for layer_value in layers:
        var layer: Variant = layer_value
        if not _exact_keys(layer, ["id", "name", "visible", "object_ids", "parallax"]):
            errors.append("scenario export layer payload is invalid")
            continue
        if typeof(layer["id"]) != TYPE_STRING or String(layer["id"]).is_empty() or String(layer["id"]).length() > 256 or layer_ids.has(layer["id"]):
            errors.append("scenario export layer IDs are invalid or duplicated")
        else:
            layer_ids[layer["id"]] = true
        if typeof(layer["name"]) != TYPE_STRING or String(layer["name"]).length() > 256 or typeof(layer["visible"]) != TYPE_BOOL:
            errors.append("scenario export layer metadata is invalid")
        var references: Variant = layer["object_ids"]
        if typeof(references) != TYPE_ARRAY or references.size() > 100000:
            errors.append("scenario export object references are invalid")
        elif typeof(references) == TYPE_ARRAY:
            for object_id in references:
                object_reference_count += 1
                if typeof(object_id) != TYPE_STRING or String(object_id).is_empty() or String(object_id).length() > 256 or object_ids.has(object_id) or object_reference_count > 100000:
                    errors.append("scenario export object references are invalid or duplicated")
                else:
                    object_ids[object_id] = true
        var parallax: Variant = layer["parallax"]
        if not _exact_keys(parallax, ["depth", "translation_strength", "zoom_strength"]):
            errors.append("scenario export parallax payload is invalid")
        elif not _unit(parallax["depth"]) or not _unit(parallax["translation_strength"]) or not _unit(parallax["zoom_strength"]):
            errors.append("scenario export parallax values are invalid")


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


static func _lower_hex_hash(value: Variant) -> bool:
    if typeof(value) != TYPE_STRING or String(value).length() != 64:
        return false
    for character in String(value):
        if not "0123456789abcdef".contains(character):
            return false
    return true


static func _unit(value: Variant) -> bool:
    return _finite(value) and float(value) >= 0.0 and float(value) <= 1.0


static func _finite(value: Variant) -> bool:
    return (typeof(value) == TYPE_FLOAT or typeof(value) == TYPE_INT) and is_finite(float(value))


static func _is_project_relative(path: String) -> bool:
    return path.begins_with("res://") and not path.contains("..")
