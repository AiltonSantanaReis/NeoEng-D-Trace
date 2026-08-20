@tool
class_name NeoEngDTraceProfessionalSceneImporter
extends RefCounted

const FORMAT_ID := "neoeng-d-trace-scene-authoring-export"
const SCHEMA_VERSION := 1
const TARGET := "godot"
const SCENE_FORMAT_ID := "neoeng-d-trace-scene-authoring"


static func diagnose_export(export_path: String) -> Dictionary:
    var result := {"status": "FAILED", "errors": []}
    if not _is_project_relative(export_path) or not FileAccess.file_exists(export_path):
        result["errors"].append("professional scene export must be an existing res:// file")
        return result
    var handle := FileAccess.open(export_path, FileAccess.READ)
    if handle == null:
        result["errors"].append("professional scene export cannot be opened")
        return result
    var payload = JSON.parse_string(handle.get_as_text())
    if typeof(payload) != TYPE_DICTIONARY:
        result["errors"].append("professional scene export JSON must be an object")
        return result
    _validate_payload(payload, result["errors"])
    if result["errors"].is_empty():
        result["status"] = "SUCCESS"
        result.erase("errors")
    return result


static func import_scene(export_path: String) -> Dictionary:
    var diagnostic := diagnose_export(export_path)
    if diagnostic.get("status") != "SUCCESS":
        return diagnostic
    var handle := FileAccess.open(export_path, FileAccess.READ)
    var payload: Dictionary = JSON.parse_string(handle.get_as_text())
    var scene_data: Dictionary = payload["scene"]
    var root := Node2D.new()
    root.name = "NeoEngProfessionalScene"
    root.set_meta("neoeng_scene_hash", str(payload["source"]["sha256"]))
    root.set_meta("neoeng_scene_name", str(scene_data["metadata"]["name"]))
    root.set_meta("neoeng_camera", scene_data["camera"])

    var assets := {}
    for asset_value in scene_data["assets"]:
        var asset: Dictionary = asset_value
        assets[asset["id"]] = asset
    var layers := {}
    for layer_value in scene_data["layers"]:
        var layer_data: Dictionary = layer_value
        var layer := Node2D.new()
        layer.name = "Layer_" + str(layer_data["id"])
        layer.visible = bool(layer_data["visible"])
        layer.set_meta("neoeng_layer_id", str(layer_data["id"]))
        layer.set_meta("neoeng_layer_name", str(layer_data["name"]))
        layer.set_meta("neoeng_layer_locked", bool(layer_data["locked"]))
        var parallax := _parallax_for(scene_data["parallax_layers"], str(layer_data["id"]))
        layer.set_meta("neoeng_parallax", parallax)
        root.add_child(layer)
        layers[layer_data["id"]] = layer

    for object_value in scene_data["objects"]:
        var object_data: Dictionary = object_value
        var layer: Node2D = layers[object_data["layer_id"]]
        var asset: Dictionary = assets[object_data["asset_id"]]
        var texture := load("res://" + str(asset["path"])) as Texture2D
        if texture == null:
            root.queue_free()
            return {"status": "FAILED", "errors": ["asset could not be loaded: " + str(asset["path"])]}
        var transform: Dictionary = object_data["transform"]
        var position: Dictionary = transform["position"]
        var rotation: Dictionary = transform["rotation"]
        var scale: Dictionary = transform["scale"]
        var sprite := Sprite2D.new()
        sprite.name = "Object_" + str(object_data["id"])
        sprite.texture = texture
        sprite.position = Vector2(float(position["x"]), float(position["y"]))
        sprite.z_index = int(round(float(position["z"])))
        sprite.rotation_degrees = float(rotation["z"])
        sprite.scale = Vector2(
            float(scale["x"]) * (-1.0 if bool(transform["flip_x"]) else 1.0),
            float(scale["y"]) * (-1.0 if bool(transform["flip_y"]) else 1.0),
        )
        sprite.visible = bool(object_data["visible"])
        sprite.set_meta("neoeng_object_id", str(object_data["id"]))
        sprite.set_meta("neoeng_asset_id", str(object_data["asset_id"]))
        sprite.set_meta("neoeng_object_locked", bool(object_data["locked"]))
        sprite.set_meta("neoeng_pivot", transform["pivot"])
        layer.add_child(sprite)

    for socket_value in scene_data["sockets"]:
        var socket: Dictionary = socket_value
        var layer: Node2D = layers[socket["layer_id"]]
        var marker := Node2D.new()
        marker.name = "Socket_" + str(socket["id"])
        marker.position = Vector2(float(socket["position"]["x"]), float(socket["position"]["y"]))
        marker.z_index = int(round(float(socket["position"]["z"])))
        marker.set_meta("neoeng_socket_id", str(socket["id"]))
        marker.set_meta("neoeng_socket_type", str(socket["type"]))
        marker.set_meta("neoeng_socket_data", socket)
        layer.add_child(marker)
    return {"status": "SUCCESS", "root": root, "payload": payload}


static func _parallax_for(records: Array, layer_id: String) -> Dictionary:
    for record_value in records:
        var record: Dictionary = record_value
        if str(record["layer_id"]) == layer_id:
            return record
    return {"layer_id": layer_id, "depth": 0.0, "translation_strength": 1.0, "zoom_strength": 1.0}


static func _validate_payload(payload: Dictionary, errors: Array) -> void:
    if not _exact_keys(payload, ["format_id", "schema_version", "target", "generator", "source", "coordinate_mapping", "capabilities", "scene"]):
        errors.append("professional scene export keys are invalid")
        return
    if payload["format_id"] != FORMAT_ID or payload["schema_version"] != SCHEMA_VERSION or payload["target"] != TARGET:
        errors.append("unsupported professional scene export format or target")
    var source: Variant = payload["source"]
    if not _exact_keys(source, ["format_id", "schema_version", "sha256"]) or source["format_id"] != SCENE_FORMAT_ID or source["schema_version"] != 2 or not _lower_hex_hash(source["sha256"]):
        errors.append("professional scene source binding is invalid")
    var mapping: Variant = payload["coordinate_mapping"]
    if not _exact_keys(mapping, ["source_origin", "target_origin", "position_y_sign", "rotation_sign", "rotation_unit"]) or mapping["source_origin"] != "top-left" or mapping["target_origin"] != "godot-2d-y-down" or mapping["position_y_sign"] != 1 or mapping["rotation_sign"] != 1 or mapping["rotation_unit"] != "degrees":
        errors.append("professional scene coordinate mapping is invalid")
    var scene: Variant = payload["scene"]
    if not _exact_keys(scene, ["format_id", "schema_version", "metadata", "project", "assets", "layers", "objects", "groups", "snap", "camera", "parallax_layers", "sockets"]) or scene["format_id"] != SCENE_FORMAT_ID or scene["schema_version"] != 2:
        errors.append("professional scene document is invalid")
        return
    var asset_ids := {}
    for asset_value in scene["assets"]:
        var asset: Variant = asset_value
        if not _exact_keys(asset, ["id", "path", "path_kind", "sha256"]) or asset["path_kind"] != "relative" or not _safe_asset_path(asset["path"]) or not _lower_hex_hash(asset["sha256"]) or asset_ids.has(asset["id"]):
            errors.append("professional scene asset references are invalid")
        else:
            asset_ids[asset["id"]] = true
            var asset_path := "res://" + str(asset["path"]);
            if not FileAccess.file_exists(asset_path):
                errors.append("professional scene asset is missing: " + str(asset["path"]))
            elif _sha256_file(asset_path) != str(asset["sha256"]):
                errors.append("professional scene asset hash does not match: " + str(asset["path"]))
    var layer_ids := {}
    for layer_value in scene["layers"]:
        var layer: Variant = layer_value
        if not _exact_keys(layer, ["id", "name", "visible", "locked"]) or typeof(layer["id"]) != TYPE_STRING or String(layer["id"]).is_empty() or layer_ids.has(layer["id"]):
            errors.append("professional scene layer references are invalid")
        else:
            layer_ids[layer["id"]] = true
    var object_ids := {}
    for object_value in scene["objects"]:
        var object: Variant = object_value
        if not _exact_keys(object, ["id", "asset_id", "layer_id", "transform", "visible", "locked"]) or object_ids.has(object["id"]) or not asset_ids.has(object["asset_id"]) or not layer_ids.has(object["layer_id"]) or not _valid_transform(object["transform"]):
            errors.append("professional scene object references are invalid")
        else:
            object_ids[object["id"]] = true
    for socket_value in scene["sockets"]:
        var socket: Variant = socket_value
        if not _valid_socket(socket, layer_ids, object_ids):
            errors.append("professional scene socket is invalid")


static func _valid_transform(value: Variant) -> bool:
    if not _exact_keys(value, ["position", "rotation", "scale", "pivot", "flip_x", "flip_y"]):
        return false
    return _vector3(value["position"]) and _vector3(value["rotation"]) and _vector3_positive(value["scale"]) and _vector2_unit(value["pivot"]) and typeof(value["flip_x"]) == TYPE_BOOL and typeof(value["flip_y"]) == TYPE_BOOL


static func _valid_socket(value: Variant, layer_ids: Dictionary, object_ids: Dictionary) -> bool:
    if typeof(value) != TYPE_DICTIONARY or not value.has("type") or not value.has("id") or not value.has("layer_id") or not value.has("position") or not layer_ids.has(value["layer_id"]) or (value["object_id"] != null and not object_ids.has(value["object_id"])) or not _vector3(value["position"]):
        return false
    if value["type"] == "light":
        return _exact_keys(value, ["id", "layer_id", "object_id", "position", "type", "color", "intensity", "radius"]) and typeof(value["color"]) == TYPE_STRING and String(value["color"]).is_valid_html_color() and _positive(value["intensity"]) and _positive(value["radius"])
    if value["type"] == "vfx":
        return _exact_keys(value, ["id", "layer_id", "object_id", "position", "type", "effect_id", "scale", "enabled"]) and typeof(value["effect_id"]) == TYPE_STRING and not String(value["effect_id"]).is_empty() and _positive(value["scale"]) and typeof(value["enabled"]) == TYPE_BOOL
    if value["type"] == "trigger":
        return _exact_keys(value, ["id", "layer_id", "object_id", "position", "type", "event_id", "size"]) and typeof(value["event_id"]) == TYPE_STRING and not String(value["event_id"]).is_empty() and _vector3_positive(value["size"])
    return false


static func _vector2_unit(value: Variant) -> bool:
    return _exact_keys(value, ["x", "y"]) and _finite(value["x"]) and _finite(value["y"]) and float(value["x"]) >= 0.0 and float(value["x"]) <= 1.0 and float(value["y"]) >= 0.0 and float(value["y"]) <= 1.0


static func _vector3(value: Variant) -> bool:
    return _exact_keys(value, ["x", "y", "z"]) and _finite(value["x"]) and _finite(value["y"]) and _finite(value["z"])


static func _vector3_positive(value: Variant) -> bool:
    return _vector3(value) and float(value["x"]) > 0.0 and float(value["y"]) > 0.0 and float(value["z"]) > 0.0


static func _positive(value: Variant) -> bool:
    return _finite(value) and float(value) > 0.0


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


static func _finite(value: Variant) -> bool:
    return (typeof(value) == TYPE_FLOAT or typeof(value) == TYPE_INT) and is_finite(float(value))


static func _sha256_file(path: String) -> String:
    var handle := FileAccess.open(path, FileAccess.READ)
    if handle == null:
        return ""
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    while not handle.eof_reached():
        context.update(handle.get_buffer(1024 * 1024))
    return context.finish().hex_encode()

static func _safe_asset_path(value: Variant) -> bool:
    if typeof(value) != TYPE_STRING:
        return false
    var path := String(value).replace("\\", "/")
    return not path.is_empty() and not path.begins_with("/") and not path.contains(":") and not path.contains("..")


static func _is_project_relative(path: String) -> bool:
    return path.begins_with("res://") and not path.contains("..")
