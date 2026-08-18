@tool
class_name NeoEngDTraceImporter
extends RefCounted

const ManifestDiagnostic = preload("res://addons/neoeng_d_trace/manifest_diagnostic.gd")


static func dry_run_manifest(manifest_path: String, output_root: String = "res://NeoEngGenerated") -> Dictionary:
    return import_manifest(manifest_path, output_root, true)


static func import_manifest(
    manifest_path: String,
    output_root: String = "res://NeoEngGenerated",
    dry_run: bool = false,
) -> Dictionary:
    var diagnostic := ManifestDiagnostic.diagnose_manifest(manifest_path)
    if diagnostic.get("status") != "SUCCESS":
        return {
            "status": "FAILED",
            "manifest_path": manifest_path,
            "errors": [diagnostic],
        }
    if not _is_project_relative(output_root):
        return _failure(manifest_path, "output root must use a safe res:// reference")
    var handle := FileAccess.open(manifest_path, FileAccess.READ)
    if handle == null:
        return _failure(manifest_path, "manifest file cannot be opened")
    var payload = JSON.parse_string(handle.get_as_text())
    if typeof(payload) != TYPE_DICTIONARY:
        return _failure(manifest_path, "manifest JSON must be an object")
    var metadata = payload.get("metadata")
    var sprites = metadata.get("sprites") if typeof(metadata) == TYPE_DICTIONARY else null
    if typeof(sprites) != TYPE_ARRAY or sprites.is_empty():
        return _failure(manifest_path, "manifest metadata contains no sprites")
    var source = payload.get("source")
    var image = source.get("image") if typeof(source) == TYPE_DICTIONARY else null
    var image_reference = image.get("path") if typeof(image) == TYPE_DICTIONARY else ""
    if not ManifestDiagnostic._is_safe_relative(image_reference):
        return _failure(manifest_path, "manifest image path is not relative and safe")
    var expected_image_hash := str(image.get("sha256", ""))
    var metadata_source = source.get("metadata") if typeof(source) == TYPE_DICTIONARY else {}
    var expected_metadata_hash := str(metadata_source.get("sha256", ""))
    var actual_image_hash := _sha256_bytes(FileAccess.get_file_as_bytes("res://" + image_reference))
    if actual_image_hash != expected_image_hash:
        return _failure(manifest_path, "manifest image hash does not match source image")
    var texture := load("res://" + image_reference) as Texture2D
    if texture == null:
        return _failure(manifest_path, "manifest image cannot be loaded")
    var advanced_validation := _validate_advanced_runtime(payload)
    if advanced_validation.get("status") != "SUCCESS":
        return _failure(manifest_path, str(advanced_validation.get("error", "advanced manifest is invalid")))
    if not dry_run and not DirAccess.dir_exists_absolute(output_root):
        var make_error := DirAccess.make_dir_recursive_absolute(output_root)
        if make_error != OK:
            return _failure(manifest_path, "generated output directory cannot be created")
    var results: Array = []
    var operations: Array = []
    for sprite_data in sprites:
        if typeof(sprite_data) != TYPE_DICTIONARY:
            return _failure(manifest_path, "sprite metadata must be an object")
        var import_data: Dictionary = sprite_data.duplicate(true)
        var advanced_entry := _advanced_entry(payload, str(sprite_data.get("id", "")))
        if advanced_entry.get("status") != "SUCCESS":
            return _failure(manifest_path, str(advanced_entry.get("error", "advanced atlas sprite is missing")))
        if advanced_entry.get("entry") != null:
            import_data["rect"] = advanced_entry["entry"].get("rect")
            import_data["_advanced_image_reference"] = advanced_entry.get("path", "")
            import_data["_advanced_page_hash"] = advanced_entry.get("sha256", "")
            import_data["_advanced_engine_properties"] = payload.get("advanced", {}).get("engine_properties", {}).get("godot", {})
            import_data["_advanced_pixels_per_unit"] = payload.get("advanced", {}).get("coordinate_system", {}).get("pixels_per_unit", {}).get("godot", 1.0)
        var result := _import_sprite(import_data, texture, manifest_path, output_root, payload, true)
        results.append(result)
        if result.get("status") == "CONFLICT" or result.get("status") == "FAILED":
            return {
                "status": result.get("status"),
                "manifest_path": manifest_path,
                "results": results,
            }
        if result.get("status") == "PLANNED":
            operations.append(result)
    if typeof(metadata) == TYPE_DICTIONARY and metadata.has("tileset"):
        var tileset_result := _import_tileset(metadata.get("tileset"), manifest_path, output_root, image_reference, expected_image_hash, expected_metadata_hash, true)
        results.append(tileset_result)
        if tileset_result.get("status") != "PLANNED" and tileset_result.get("status") != "UPDATED" and tileset_result.get("status") != "UNCHANGED":
            return {
                "status": tileset_result.get("status"),
                "manifest_path": manifest_path,
                "results": results,
            }
        if tileset_result.get("status") == "PLANNED":
            operations.append(tileset_result)
    if typeof(metadata) == TYPE_DICTIONARY and metadata.has("animation"):
        var animation_result := _import_animation(metadata.get("animation"), manifest_path, output_root, expected_image_hash, expected_metadata_hash, true)
        results.append(animation_result)
        if animation_result.get("status") != "PLANNED" and animation_result.get("status") != "UPDATED" and animation_result.get("status") != "UNCHANGED":
            return {
                "status": animation_result.get("status"),
                "manifest_path": manifest_path,
                "results": results,
            }
        if animation_result.get("status") == "PLANNED":
            operations.append(animation_result)
    if dry_run:
        for planned in operations:
            planned.erase("content")
        return {
            "status": "DRY_RUN",
            "manifest_path": manifest_path,
            "output_root": output_root,
            "results": results,
        }
    var commit_result := _commit_operations(operations, output_root)
    if commit_result.get("status") != "SUCCESS":
        return {
            "status": "FAILED",
            "manifest_path": manifest_path,
            "results": results,
            "errors": [commit_result.get("error", "generated output transaction failed")],
        }
    for applied in results:
        if applied.get("status") == "PLANNED":
            applied["status"] = "UPDATED"
            applied.erase("content")
    return {
        "status": "SUCCESS",
        "manifest_path": manifest_path,
        "output_root": output_root,
        "results": results,
    }


static func import_project(root: String = "res://NeoEngGenerated") -> Dictionary:
    var scan := ManifestDiagnostic.scan_project(root)
    if scan.get("status") != "SUCCESS":
        return scan
    var snapshot := _snapshot_tree(root)
    var results: Array = []
    var manifest_results: Array = scan.get("manifests", []).duplicate(true)
    manifest_results.sort_custom(func(left: Dictionary, right: Dictionary):
        return str(left.get("manifest_path", "")) < str(right.get("manifest_path", ""))
    )
    for manifest_result in manifest_results:
        var manifest_path = manifest_result.get("manifest_path", "")
        var result := import_manifest(manifest_path, root)
        results.append(result)
        if result.get("status") != "SUCCESS":
            if not _restore_tree(root, snapshot):
                return {
                    "status": "FAILED",
                    "transaction": "GLOBAL",
                    "rollback": "FAILED",
                    "results": results,
                }
            return {
                "status": "FAILED",
                "transaction": "GLOBAL",
                "rollback": "RESTORED",
                "results": results,
            }
    return {
        "status": "SUCCESS",
        "transaction": "GLOBAL",
        "rollback": "NOT_REQUIRED",
        "root": root,
        "results": results,
    }


static func _snapshot_tree(root: String) -> Dictionary:
    var snapshot := {"exists": DirAccess.dir_exists_absolute(root), "files": {}}
    if snapshot["exists"]:
        var files: Dictionary = snapshot["files"]
        _collect_tree_files(root, root, files)
    return snapshot


static func _collect_tree_files(root: String, current: String, files: Dictionary) -> void:
    for file_name in DirAccess.get_files_at(current):
        var path := current.path_join(file_name)
        var relative := path.trim_prefix(root).trim_prefix("/")
        files[relative] = FileAccess.get_file_as_bytes(path)
    var directories := DirAccess.get_directories_at(current)
    directories.sort()
    for directory_name in directories:
        _collect_tree_files(root, current.path_join(directory_name), files)


static func _restore_tree(root: String, snapshot: Dictionary) -> bool:
    if DirAccess.dir_exists_absolute(root) and not _remove_tree(root):
        return false
    if not bool(snapshot.get("exists", false)):
        return true
    if DirAccess.make_dir_recursive_absolute(root) != OK:
        return false
    var files: Dictionary = snapshot.get("files", {})
    var paths: Array = files.keys()
    paths.sort()
    for relative in paths:
        var destination := root.path_join(str(relative))
        var parent := destination.get_base_dir()
        if DirAccess.make_dir_recursive_absolute(parent) != OK:
            return false
        var handle := FileAccess.open(destination, FileAccess.WRITE)
        if handle == null:
            return false
        handle.store_buffer(files[relative])
        handle.close()
    return true


static func _remove_tree(path: String) -> bool:
    for file_name in DirAccess.get_files_at(path):
        if DirAccess.remove_absolute(path.path_join(file_name)) != OK:
            return false
    var directories := DirAccess.get_directories_at(path)
    directories.sort()
    for directory_name in directories:
        if not _remove_tree(path.path_join(directory_name)):
            return false
    return DirAccess.remove_absolute(path) == OK


static func _import_sprite(
    sprite_data: Dictionary,
    _texture: Texture2D,
    manifest_path: String,
    output_root: String,
    payload: Dictionary,
    plan_only: bool = false,
) -> Dictionary:
    var object_id = sprite_data.get("id")
    if typeof(object_id) != TYPE_STRING or object_id.is_empty() or not _is_safe_name(object_id):
        return {"status": "FAILED", "error": "sprite id is not safe"}
    var rect = sprite_data.get("rect")
    var pivot = sprite_data.get("pivot")
    if typeof(rect) != TYPE_DICTIONARY or typeof(pivot) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "sprite rect or pivot is invalid", "id": object_id}
    var width := float(rect.get("w", -1.0))
    var height := float(rect.get("h", -1.0))
    var rect_x := float(rect.get("x", -1.0))
    var rect_y := float(rect.get("y", -1.0))
    var pivot_x := float(pivot.get("x", -1.0))
    var pivot_y := float(pivot.get("y", -1.0))
    if width <= 0.0 or height <= 0.0 or rect_x < 0.0 or rect_y < 0.0:
        return {"status": "FAILED", "error": "sprite rect is invalid", "id": object_id}
    if pivot_x < 0.0 or pivot_y < 0.0 or pivot_x > width or pivot_y > height:
        return {"status": "FAILED", "error": "sprite pivot is outside the rect", "id": object_id}
    var properties := _sprite_properties(sprite_data)
    if properties.get("status") != "SUCCESS":
        return properties
    var destination := output_root.path_join(object_id + ".tscn")
    var source = payload.get("source", {})
    var image_source = source.get("image", {}) if typeof(source) == TYPE_DICTIONARY else {}
    var metadata_source = source.get("metadata", {}) if typeof(source) == TYPE_DICTIONARY else {}
    var image_hash := str(image_source.get("sha256", ""))
    var metadata_hash := str(metadata_source.get("sha256", ""))
    var override := _read_override(output_root, object_id)
    if override.get("status") != "SUCCESS":
        return {"status": override.get("status", "FAILED"), "id": object_id, "error": override.get("error", "override is invalid")}
    var collision = sprite_data.get("collision")
    if override.get("polygon") != null:
        collision = {"shape_type": "polygon", "points": override.get("polygon")}
    var polygons: Array = []
    if typeof(collision) == TYPE_DICTIONARY:
        polygons = _collision_polygons(collision, rect_x, rect_y, pivot_x, pivot_y)
    var scene_template := _build_scene_text(
        object_id,
        manifest_path,
        _sprite_image_reference(sprite_data, payload),
        payload.get("generator", {}).get("version", ""),
        image_hash,
        metadata_hash,
        str(override.get("hash", "")),
        "",
        rect_x,
        rect_y,
        width,
        height,
        pivot_x,
        pivot_y,
        polygons,
        properties,
    )
    var expected_fingerprint := _fingerprint(scene_template)
    var scene_text := _set_fingerprint(scene_template, expected_fingerprint)
    if FileAccess.file_exists(destination):
        var existing := FileAccess.get_file_as_string(destination)
        if not existing.contains("metadata/neoeng_generated = true"):
            return {"status": "CONFLICT", "id": object_id, "path": destination, "error": "manual resource is not generated"}
        var stored_fingerprint := _metadata_string(existing, "neoeng_generated_fingerprint")
        var actual_fingerprint := _fingerprint(existing)
        if stored_fingerprint.is_empty() or _metadata_string(existing, "neoeng_source_image_sha256").is_empty() or _metadata_string(existing, "neoeng_source_metadata_sha256").is_empty():
            if not _destructive_update_confirmed():
                return {"status": "CONFLICT", "id": object_id, "path": destination, "error": "generated resource has no synchronization state"}
        elif actual_fingerprint != stored_fingerprint:
            if not _destructive_update_confirmed():
                return {"status": "CONFLICT", "id": object_id, "path": destination, "error": "manual divergence requires destructive update confirmation"}
        elif _metadata_string(existing, "neoeng_source_image_sha256") == image_hash and _metadata_string(existing, "neoeng_source_metadata_sha256") == metadata_hash and _metadata_string(existing, "neoeng_override_sha256") == str(override.get("hash", "")) and stored_fingerprint == expected_fingerprint:
            return {"status": "UNCHANGED", "id": object_id, "path": destination, "override_applied": override.get("polygon") != null}
    if plan_only:
        return {"status": "PLANNED", "id": object_id, "path": destination, "content": scene_text, "override_applied": override.get("polygon") != null}
    return {"status": "FAILED", "id": object_id, "path": destination, "error": "internal import plan was not committed"}


static func _read_override(output_root: String, object_id: String) -> Dictionary:
    var path := output_root.path_join(object_id + ".ndt.override.json")
    if not FileAccess.file_exists(path):
        return {"status": "SUCCESS", "polygon": null, "hash": ""}
    var text := FileAccess.get_file_as_string(path)
    var payload = JSON.parse_string(text)
    if typeof(payload) != TYPE_DICTIONARY or payload.get("object_id") != object_id:
        return {"status": "FAILED", "error": "override object id is invalid"}
    var points = payload.get("polygon_in_sprite")
    if typeof(points) != TYPE_ARRAY or points.size() < 3:
        return {"status": "FAILED", "error": "override polygon is invalid"}
    for point in points:
        if typeof(point) != TYPE_ARRAY or point.size() != 2 or not is_finite(float(point[0])) or not is_finite(float(point[1])):
            return {"status": "FAILED", "error": "override polygon contains invalid coordinates"}
    return {"status": "SUCCESS", "polygon": points, "hash": _sha256_bytes(text.to_utf8_buffer())}


static func _sha256_bytes(data: PackedByteArray) -> String:
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    context.update(data)
    return context.finish().hex_encode()

static func _fingerprint(text: String) -> String:
    return _sha256_bytes(_without_fingerprint(text).to_utf8_buffer())


static func _without_fingerprint(text: String) -> String:
    var normalized := PackedStringArray()
    for item in text.split("\n"):
        if item.begins_with("metadata/neoeng_generated_fingerprint = "):
            normalized.append("metadata/neoeng_generated_fingerprint = " + _quote(""))
        else:
            normalized.append(item)
    return "\n".join(normalized)

static func _set_fingerprint(text: String, fingerprint: String) -> String:
    return text.replace("metadata/neoeng_generated_fingerprint = %s" % _quote(""), "metadata/neoeng_generated_fingerprint = " + _quote(fingerprint))


static func _metadata_string(text: String, key: String) -> String:
    var prefix := "metadata/" + key + " = "
    for line in text.split("\n"):
        if line.begins_with(prefix):
            var value = line.trim_prefix(prefix).strip_edges()
            if value.begins_with("\"") and value.ends_with("\""):
                return str(JSON.parse_string(value))
            return value
    return ""


static func _destructive_update_confirmed() -> bool:
    var value := OS.get_environment("NEOENG_STAGE7_CONFIRM_DESTRUCTIVE").to_lower()
    return value == "1" or value == "true"

static func _validate_advanced_runtime(payload: Dictionary) -> Dictionary:
    if int(payload.get("schema_version", 1)) != 2:
        return {"status": "SUCCESS"}
    var advanced = payload.get("advanced", {})
    var pages = advanced.get("atlas", {}).get("pages", []) if typeof(advanced) == TYPE_DICTIONARY else []
    for page in pages:
        var path := str(page.get("path", ""))
        if not ManifestDiagnostic._is_safe_relative(path):
            return {"status": "FAILED", "error": "advanced atlas page path is unsafe"}
        var bytes := FileAccess.get_file_as_bytes("res://" + path)
        if bytes.is_empty() or _sha256_bytes(bytes) != str(page.get("sha256", "")):
            return {"status": "FAILED", "error": "advanced atlas page hash does not match source"}
        var page_texture := load("res://" + path) as Texture2D
        if page_texture == null:
            return {"status": "FAILED", "error": "advanced atlas page cannot be loaded"}
        if page_texture.get_width() != int(page.get("width", -1)) or page_texture.get_height() != int(page.get("height", -1)):
            return {"status": "FAILED", "error": "advanced atlas page dimensions do not match manifest"}
    return {"status": "SUCCESS"}


static func _advanced_entry(payload: Dictionary, object_id: String) -> Dictionary:
    if int(payload.get("schema_version", 1)) != 2:
        return {"status": "SUCCESS", "entry": null}
    var pages = payload.get("advanced", {}).get("atlas", {}).get("pages", [])
    for page in pages:
        for entry in page.get("sprites", []):
            if str(entry.get("id", "")) == object_id:
                return {"status": "SUCCESS", "entry": entry, "path": str(page.get("path", "")), "sha256": str(page.get("sha256", ""))}
    return {"status": "FAILED", "error": "advanced atlas sprite is missing: " + object_id}


static func _sprite_image_reference(sprite_data: Dictionary, payload: Dictionary) -> String:
    var advanced_reference := str(sprite_data.get("_advanced_image_reference", ""))
    return advanced_reference if not advanced_reference.is_empty() else _image_reference_from_manifest(payload)

static func _sprite_properties(sprite_data: Dictionary) -> Dictionary:
    var layer = sprite_data.get("layer", "layer_default")
    if typeof(layer) != TYPE_STRING or layer.is_empty() or not _is_safe_name(layer):
        return {"status": "FAILED", "error": "sprite layer is not safe"}
    var group = sprite_data.get("group")
    if group != null and (typeof(group) != TYPE_STRING or not _is_safe_name(group)):
        return {"status": "FAILED", "error": "sprite group is not safe"}
    var padding_value := float(sprite_data.get("padding", 0))
    if not is_finite(padding_value) or padding_value < 0.0 or not is_equal_approx(padding_value, round(padding_value)):
        return {"status": "FAILED", "error": "sprite padding is invalid"}
    var padding := int(round(padding_value))
    var pivot_normalized = sprite_data.get("pivot_normalized", {"x": 0.5, "y": 0.5})
    if typeof(pivot_normalized) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "sprite normalized pivot is invalid"}
    var normalized_x := float(pivot_normalized.get("x", -1.0))
    var normalized_y := float(pivot_normalized.get("y", -1.0))
    if not is_finite(normalized_x) or not is_finite(normalized_y):
        return {"status": "FAILED", "error": "sprite normalized pivot is invalid"}
    var advanced_properties = sprite_data.get("_advanced_engine_properties", {})
    var texture_filter := str(advanced_properties.get("texture_filter", "nearest"))
    var texture_repeat := str(advanced_properties.get("texture_repeat", "disabled"))
    var centered := bool(advanced_properties.get("centered", true))
    var z_index_value := int(advanced_properties.get("z_index", 0))
    if texture_filter != "nearest" and texture_filter != "linear":
        return {"status": "FAILED", "error": "advanced Godot texture filter is invalid"}
    if texture_repeat != "disabled" and texture_repeat != "enabled":
        return {"status": "FAILED", "error": "advanced Godot texture repeat is invalid"}
    var pixels_per_unit := float(sprite_data.get("_advanced_pixels_per_unit", 1.0))
    if not is_finite(pixels_per_unit) or pixels_per_unit <= 0.0:
        return {"status": "FAILED", "error": "advanced Godot pixels per unit is invalid"}
    return {
        "status": "SUCCESS",
        "layer": layer,
        "group": "" if group == null else str(group),
        "trimmed": bool(sprite_data.get("trimmed", false)),
        "padding": padding,
        "pivot_normalized_x": normalized_x,
        "pivot_normalized_y": normalized_y,
        "texture_filter": texture_filter,
        "texture_repeat": texture_repeat,
        "centered": centered,
        "z_index": z_index_value,
        "pixels_per_unit": pixels_per_unit,
        "advanced_page_hash": str(sprite_data.get("_advanced_page_hash", "")),
    }


static func _import_tileset(
    tileset_data,
    manifest_path: String,
    output_root: String,
    image_reference: String,
    source_image_hash: String,
    source_metadata_hash: String,
    plan_only: bool = false,
) -> Dictionary:
    if typeof(tileset_data) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "tileset payload must be an object"}
    if tileset_data.get("format_id") != "neoeng-d-trace-tileset" or tileset_data.get("schema_version") != 1:
        return {"status": "FAILED", "error": "unsupported tileset payload"}
    var tile_size = tileset_data.get("tile_size")
    if typeof(tile_size) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "tileset tile size is invalid"}
    var tile_w := int(tile_size.get("w", 0))
    var tile_h := int(tile_size.get("h", 0))
    var spacing := int(tileset_data.get("spacing", 0))
    var margin := int(tileset_data.get("margin", 0))
    if tile_w <= 0 or tile_h <= 0 or spacing < 0 or margin < 0:
        return {"status": "FAILED", "error": "tileset grid is invalid"}
    var tiles = tileset_data.get("tiles")
    if typeof(tiles) != TYPE_ARRAY or tiles.is_empty():
        return {"status": "FAILED", "error": "tileset contains no tiles"}
    for tile in tiles:
        var tile_error := _validate_tile(tile, tile_w, tile_h)
        if tile_error != "":
            return {"status": "FAILED", "error": tile_error}
    var destination := output_root.path_join("tileset.tres")
    var resource_text := _build_tileset_text(
        manifest_path,
        image_reference,
        source_image_hash,
        source_metadata_hash,
        tile_w,
        tile_h,
        spacing,
        margin,
        tiles,
    )
    var result := _synchronize_generated(destination, resource_text, source_image_hash, source_metadata_hash, "", plan_only)
    result["path"] = destination
    result["tile_count"] = tiles.size()
    return result


static func _synchronize_generated(
    destination: String,
    template: String,
    source_image_hash: String,
    source_metadata_hash: String,
    override_hash: String = "",
    plan_only: bool = false,
) -> Dictionary:
    var expected_fingerprint := _fingerprint(template)
    var generated_text := _set_fingerprint(template, expected_fingerprint)
    if FileAccess.file_exists(destination):
        var existing := FileAccess.get_file_as_string(destination)
        if not existing.contains("metadata/neoeng_generated = true"):
            return {"status": "CONFLICT", "path": destination, "error": "manual resource is not generated"}
        var stored_fingerprint := _metadata_string(existing, "neoeng_generated_fingerprint")
        var actual_fingerprint := _fingerprint(existing)
        if stored_fingerprint.is_empty() or _metadata_string(existing, "neoeng_source_image_sha256").is_empty() or _metadata_string(existing, "neoeng_source_metadata_sha256").is_empty():
            if not _destructive_update_confirmed():
                return {"status": "CONFLICT", "path": destination, "error": "generated resource has no synchronization state"}
        elif actual_fingerprint != stored_fingerprint:
            if not _destructive_update_confirmed():
                return {"status": "CONFLICT", "path": destination, "error": "manual divergence requires destructive update confirmation"}
        elif _metadata_string(existing, "neoeng_source_image_sha256") == source_image_hash and _metadata_string(existing, "neoeng_source_metadata_sha256") == source_metadata_hash and _metadata_string(existing, "neoeng_override_sha256") == override_hash and stored_fingerprint == expected_fingerprint:
            return {"status": "UNCHANGED", "path": destination}
    if plan_only:
        return {"status": "PLANNED", "path": destination, "content": generated_text}
    return {"status": "FAILED", "path": destination, "error": "internal import plan was not committed"}

static func _validate_tile(tile, tile_w: int, tile_h: int) -> String:
    if typeof(tile) != TYPE_DICTIONARY:
        return "tileset tile must be an object"
    var tile_id = tile.get("id")
    if typeof(tile_id) != TYPE_STRING or tile_id.is_empty() or not _is_safe_name(tile_id):
        return "tileset tile id is not safe"
    var rect = tile.get("source_rect")
    if typeof(rect) != TYPE_DICTIONARY:
        return "tileset source rect is invalid"
    if int(rect.get("w", 0)) != tile_w or int(rect.get("h", 0)) != tile_h:
        return "tileset source rect does not match tile size"
    if int(rect.get("x", -1)) < 0 or int(rect.get("y", -1)) < 0:
        return "tileset source rect is outside the image"
    var collision = tile.get("collision")
    if collision == null:
        return ""
    if typeof(collision) != TYPE_ARRAY or collision.size() < 3:
        return "tileset collision is invalid"
    for point in collision:
        if typeof(point) != TYPE_ARRAY or point.size() != 2:
            return "tileset collision point is invalid"
        if not is_finite(float(point[0])) or not is_finite(float(point[1])):
            return "tileset collision point is invalid"
    return ""


static func _import_animation(
    animation_data,
    manifest_path: String,
    output_root: String,
    source_image_hash: String,
    source_metadata_hash: String,
    plan_only: bool = false,
) -> Dictionary:
    if typeof(animation_data) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "animation payload must be an object"}
    if animation_data.get("format_id") != "neoeng-d-trace-animation" or animation_data.get("schema_version") != 1:
        return {"status": "FAILED", "error": "unsupported animation payload"}
    var frames = animation_data.get("frames")
    if typeof(frames) != TYPE_ARRAY or frames.is_empty():
        return {"status": "FAILED", "error": "animation contains no frames"}
    if int(animation_data.get("frame_count", frames.size())) != frames.size():
        return {"status": "FAILED", "error": "animation frame count is inconsistent"}
    var frame_descriptors: Array = []
    for frame in frames:
        var descriptor := _validate_animation_frame(frame)
        if descriptor.get("status") != "SUCCESS":
            return descriptor
        frame_descriptors.append(descriptor)
    var destination := output_root.path_join("animation.tscn")
    var speed := float(animation_data.get("speed", 12.0))
    if not is_finite(speed) or speed <= 0.0:
        return {"status": "FAILED", "error": "animation speed is invalid"}
    var scene_text := _build_animation_text(manifest_path, source_image_hash, source_metadata_hash, frame_descriptors, speed, bool(animation_data.get("loop", true)))
    var result := _synchronize_generated(destination, scene_text, source_image_hash, source_metadata_hash, "", plan_only)
    result["path"] = destination
    result["frame_count"] = frame_descriptors.size()
    return result


static func _validate_animation_frame(frame) -> Dictionary:
    if typeof(frame) != TYPE_DICTIONARY:
        return {"status": "FAILED", "error": "animation frame must be an object"}
    var texture_path = frame.get("texture")
    if typeof(texture_path) != TYPE_STRING or not ManifestDiagnostic._is_safe_relative(texture_path):
        return {"status": "FAILED", "error": "animation frame texture path is unsafe"}
    var texture := load("res://" + texture_path) as Texture2D
    if texture == null:
        return {"status": "FAILED", "error": "animation frame texture cannot be loaded"}
    var size = frame.get("size")
    if typeof(size) != TYPE_DICTIONARY or int(size.get("w", 0)) <= 0 or int(size.get("h", 0)) <= 0:
        return {"status": "FAILED", "error": "animation frame size is invalid"}
    var polygon = frame.get("polygon", [])
    if polygon != null and (typeof(polygon) != TYPE_ARRAY or (not polygon.is_empty() and polygon.size() < 3)):
        return {"status": "FAILED", "error": "animation frame polygon is invalid"}
    return {
        "status": "SUCCESS",
        "texture": texture_path,
        "width": int(size.get("w")),
        "height": int(size.get("h")),
        "polygon": [] if polygon == null else polygon,
    }


static func _build_scene_text(
    object_id: String,
    manifest_path: String,
    image_reference: String,
    generator_version: String,
    source_image_hash: String,
    source_metadata_hash: String,
    override_hash: String,
    fingerprint: String,
    rect_x: float,
    rect_y: float,
    width: float,
    height: float,
    pivot_x: float,
    pivot_y: float,
    polygons: Array,
    properties: Dictionary,
) -> String:
    var lines := PackedStringArray()
    lines.append("[gd_scene format=3]")
    lines.append("")
    lines.append("[ext_resource type=\"Texture2D\" path=%s id=\"1_texture\"]" % _quote("res://" + image_reference))
    lines.append("")
    lines.append("[sub_resource type=\"AtlasTexture\" id=\"AtlasTexture_1\"]")
    lines.append("atlas = ExtResource(\"1_texture\")")
    lines.append("region = Rect2(%s, %s, %s, %s)" % [_number(rect_x), _number(rect_y), _number(width), _number(height)])
    lines.append("")
    lines.append("[node name=%s type=\"Node2D\"]" % _quote("NeoEngGenerated_" + object_id))
    lines.append("metadata/neoeng_generated = true")
    lines.append("metadata/neoeng_manifest = %s" % _quote(manifest_path))
    lines.append("metadata/neoeng_object_id = %s" % _quote(object_id))
    lines.append("metadata/neoeng_generator_version = %s" % _quote(generator_version))
    lines.append("metadata/neoeng_source_image_sha256 = %s" % _quote(source_image_hash))
    lines.append("metadata/neoeng_source_metadata_sha256 = %s" % _quote(source_metadata_hash))
    lines.append("metadata/neoeng_override_sha256 = %s" % _quote(override_hash))
    lines.append("metadata/neoeng_generated_fingerprint = %s" % _quote(fingerprint))
    lines.append("metadata/neoeng_layer = %s" % _quote(properties.get("layer", "")))
    lines.append("metadata/neoeng_group = %s" % _quote(properties.get("group", "")))
    lines.append("metadata/neoeng_trimmed = %s" % str(properties.get("trimmed", false)).to_lower())
    lines.append("metadata/neoeng_padding = %d" % int(properties.get("padding", 0)))
    lines.append("metadata/neoeng_advanced_page_sha256 = %s" % _quote(str(properties.get("advanced_page_hash", ""))))
    lines.append("")
    lines.append("[node name=\"Sprite2D\" type=\"Sprite2D\" parent=\".\"]")
    lines.append("texture = SubResource(\"AtlasTexture_1\")")
    lines.append("centered = %s" % str(bool(properties.get("centered", true))).to_lower())
    lines.append("texture_filter = %d" % (1 if properties.get("texture_filter", "nearest") == "nearest" else 2))
    lines.append("texture_repeat = %d" % (0 if properties.get("texture_repeat", "disabled") == "disabled" else 1))
    lines.append("z_index = %d" % int(properties.get("z_index", 0)))
    var pixels_per_unit := float(properties.get("pixels_per_unit", 1.0))
    lines.append("scale = Vector2(%s, %s)" % [_number(1.0 / pixels_per_unit), _number(1.0 / pixels_per_unit)])
    lines.append("offset = Vector2(%s, %s)" % [_number((width * 0.5 - pivot_x) / pixels_per_unit), _number((height * 0.5 - pivot_y) / pixels_per_unit)])
    lines.append("metadata/neoeng_generated = true")
    lines.append("metadata/neoeng_pivot_pixels = Vector2(%s, %s)" % [_number(pivot_x), _number(pivot_y)])
    lines.append("metadata/neoeng_pivot_normalized = Vector2(%s, %s)" % [_number(properties.get("pivot_normalized_x", 0.5)), _number(properties.get("pivot_normalized_y", 0.5))])
    for index in polygons.size():
        var node_name := "CollisionPolygon2D" if polygons.size() == 1 else "CollisionPolygon2D_%d" % index
        lines.append("")
        lines.append("[node name=%s type=\"CollisionPolygon2D\" parent=\".\"]" % _quote(node_name))
        lines.append("polygon = %s" % _packed_vector2_array_scaled(polygons[index], float(properties.get("pixels_per_unit", 1.0))))
        lines.append("metadata/neoeng_generated = true")
    return "\n".join(lines) + "\n"


static func _build_tileset_text(
    manifest_path: String,
    image_reference: String,
    source_image_hash: String,
    source_metadata_hash: String,
    tile_w: int,
    tile_h: int,
    spacing: int,
    margin: int,
    tiles: Array,
) -> String:
    var lines := PackedStringArray()
    lines.append("[gd_resource type=\"TileSet\" load_steps=3 format=3]")
    lines.append("")
    lines.append("[ext_resource type=\"Texture2D\" path=%s id=\"1_texture\"]" % _quote("res://" + image_reference))
    lines.append("")
    lines.append("[sub_resource type=\"TileSetAtlasSource\" id=\"TileSetAtlasSource_1\"]")
    lines.append("texture = ExtResource(\"1_texture\")")
    lines.append("texture_region_size = Vector2i(%d, %d)" % [tile_w, tile_h])
    lines.append("margins = Vector2i(%d, %d)" % [margin, margin])
    lines.append("separation = Vector2i(%d, %d)" % [spacing, spacing])
    for tile in tiles:
        var column := int(tile.get("column", 0))
        var row := int(tile.get("row", 0))
        lines.append("%d:%d/0 = 0" % [column, row])
        var collision = tile.get("collision")
        if collision != null:
            lines.append("%d:%d/0/physics_layer_0/polygon_0/points = %s" % [column, row, _packed_vector2_array_from_points(collision)])
    lines.append("")
    lines.append("[resource]")
    lines.append("tile_size = Vector2i(%d, %d)" % [tile_w, tile_h])
    lines.append("physics_layer_0/collision_layer = 1")
    lines.append("physics_layer_0/collision_mask = 1")
    lines.append("metadata/neoeng_generated = true")
    lines.append("metadata/neoeng_manifest = %s" % _quote(manifest_path))
    lines.append("metadata/neoeng_source_image_sha256 = %s" % _quote(source_image_hash))
    lines.append("metadata/neoeng_source_metadata_sha256 = %s" % _quote(source_metadata_hash))
    lines.append("metadata/neoeng_override_sha256 = %s" % _quote(""))
    lines.append("metadata/neoeng_generated_fingerprint = %s" % _quote(""))
    lines.append("sources/0 = SubResource(\"TileSetAtlasSource_1\")")
    return "\n".join(lines) + "\n"


static func _build_animation_text(
    manifest_path: String,
    source_image_hash: String,
    source_metadata_hash: String,
    frames: Array,
    speed: float,
    loop: bool,
) -> String:
    var lines := PackedStringArray()
    var has_collisions := false
    for frame in frames:
        if not frame.get("polygon", []).is_empty():
            has_collisions = true
    lines.append("[gd_scene load_steps=%d format=3]" % (frames.size() + (2 if has_collisions else 1)))
    lines.append("")
    if has_collisions:
        lines.append("[ext_resource type=\"Script\" path=\"res://addons/neoeng_d_trace/animation_collision_driver.gd\" id=\"1_driver\"]")
    for index in frames.size():
        var resource_id := "%d_frame_%d" % [2 if has_collisions else 1, index]
        lines.append("[ext_resource type=\"Texture2D\" path=%s id=\"%s\"]" % [_quote("res://" + frames[index].get("texture")), resource_id])
    lines.append("")
    lines.append("[sub_resource type=\"SpriteFrames\" id=\"SpriteFrames_1\"]")
    lines.append("animations = [{")
    lines.append("\"frames\": [{")
    for index in frames.size():
        var resource_id := "%d_frame_%d" % [2 if has_collisions else 1, index]
        lines.append("\"duration\": 1.0,")
        lines.append("\"texture\": ExtResource(\"%s\")" % resource_id)
        if index < frames.size() - 1:
            lines.append("}, {")
        else:
            lines.append("}],")
    lines.append("\"loop\": %s," % str(loop).to_lower())
    lines.append("\"name\": &\"default\",")
    lines.append("\"speed\": %s" % _number(speed))
    lines.append("}]")
    lines.append("")
    lines.append("[node name=\"NeoEngGenerated_Animation\" type=\"Node2D\"]")
    lines.append("metadata/neoeng_generated = true")
    lines.append("metadata/neoeng_source_image_sha256 = %s" % _quote(source_image_hash))
    lines.append("metadata/neoeng_source_metadata_sha256 = %s" % _quote(source_metadata_hash))
    lines.append("metadata/neoeng_override_sha256 = %s" % _quote(""))
    lines.append("metadata/neoeng_generated_fingerprint = %s" % _quote(""))
    lines.append("metadata/neoeng_manifest = %s" % _quote(manifest_path))
    lines.append("metadata/neoeng_animation_frame_count = %d" % frames.size())
    if has_collisions:
        lines.append("script = ExtResource(\"1_driver\")")
    lines.append("")
    lines.append("[node name=\"AnimatedSprite2D\" type=\"AnimatedSprite2D\" parent=\".\"]")
    lines.append("sprite_frames = SubResource(\"SpriteFrames_1\")")
    lines.append("animation = &\"default\"")
    lines.append("autoplay = \"default\"")
    for index in frames.size():
        var polygon = frames[index].get("polygon", [])
        if polygon.is_empty():
            continue
        lines.append("")
        lines.append("[node name=\"AnimationCollision_%d\" type=\"CollisionPolygon2D\" parent=\".\"]" % index)
        lines.append("disabled = %s" % ("false" if index == 0 else "true"))
        lines.append("polygon = %s" % _packed_vector2_array_relative(polygon, float(frames[index].get("width")) * 0.5, float(frames[index].get("height")) * 0.5))
        lines.append("metadata/neoeng_generated = true")
        lines.append("metadata/neoeng_animation_frame = %d" % index)
    return "\n".join(lines) + "\n"


static func _commit_operations(operations: Array, output_root: String) -> Dictionary:
    if operations.is_empty():
        return {"status": "SUCCESS"}
    if not _is_project_relative(output_root):
        return {"status": "FAILED", "error": "generated output root is unsafe"}
    if not DirAccess.dir_exists_absolute(output_root):
        var make_error := DirAccess.make_dir_recursive_absolute(output_root)
        if make_error != OK:
            return {"status": "FAILED", "error": "generated output directory cannot be created"}
    var staged: Array = []
    var prefix := output_root.trim_suffix("/") + "/"
    for index in operations.size():
        var operation = operations[index]
        var destination := str(operation.get("path", ""))
        if not destination.begins_with(prefix) or destination.contains(".."):
            return {"status": "FAILED", "error": "generated output destination is unsafe"}
        var temporary := destination + ".neoeng-stage9-tmp"
        var backup := destination + ".neoeng-stage9-backup"
        if FileAccess.file_exists(temporary) or FileAccess.file_exists(backup):
            return {"status": "FAILED", "error": "staging path already exists"}
        var staged_file := FileAccess.open(temporary, FileAccess.WRITE)
        if staged_file == null:
            return {"status": "FAILED", "error": "generated resource could not be staged"}
        staged_file.store_string(str(operation.get("content", "")))
        staged_file.close()
        staged.append({
            "destination": destination,
            "temporary": temporary,
            "backup": backup,
            "backed_up": false,
            "committed": false,
        })
    for index in staged.size():
        var item: Dictionary = staged[index]
        var destination := str(item["destination"])
        if FileAccess.file_exists(destination):
            if DirAccess.rename_absolute(destination, str(item["backup"])) != OK:
                _rollback_operations(staged)
                return {"status": "FAILED", "error": "existing generated output could not be backed up"}
            item["backed_up"] = true
        if DirAccess.rename_absolute(str(item["temporary"]), destination) != OK:
            _rollback_operations(staged)
            return {"status": "FAILED", "error": "generated output could not be committed"}
        item["committed"] = true
    _cleanup_operations(staged)
    return {"status": "SUCCESS"}


static func _rollback_operations(staged: Array) -> void:
    for index in range(staged.size() - 1, -1, -1):
        var item: Dictionary = staged[index]
        var destination := str(item["destination"])
        var backup := str(item["backup"])
        if bool(item.get("committed", false)) and FileAccess.file_exists(destination):
            DirAccess.remove_absolute(destination)
        if bool(item.get("backed_up", false)) and FileAccess.file_exists(backup):
            DirAccess.rename_absolute(backup, destination)
    _cleanup_operations(staged)


static func _cleanup_operations(staged: Array) -> void:
    for item in staged:
        var temporary := str(item["temporary"])
        var backup := str(item["backup"])
        if FileAccess.file_exists(temporary):
            DirAccess.remove_absolute(temporary)
        if FileAccess.file_exists(backup):
            DirAccess.remove_absolute(backup)

static func _write_generated(destination: String, text: String) -> Dictionary:
    var temporary := destination + ".tmp"
    var scene_file := FileAccess.open(temporary, FileAccess.WRITE)
    if scene_file == null:
        return {"status": "FAILED", "error": "generated resource could not be saved"}
    scene_file.store_string(text)
    scene_file.close()
    if FileAccess.file_exists(destination):
        var remove_error := DirAccess.remove_absolute(destination)
        if remove_error != OK:
            DirAccess.remove_absolute(temporary)
            return {"status": "FAILED", "error": "generated resource could not replace prior output"}
    var rename_error := DirAccess.rename_absolute(temporary, destination)
    if rename_error != OK:
        DirAccess.remove_absolute(temporary)
        return {"status": "FAILED", "error": "generated resource could not be committed"}
    return {"status": "UPDATED"}


static func _packed_vector2_array_from_points(points: Array) -> String:
    var polygon := PackedVector2Array()
    for point in points:
        polygon.append(Vector2(float(point[0]), float(point[1])))
    return _packed_vector2_array(polygon)


static func _packed_vector2_array_relative(points: Array, offset_x: float, offset_y: float) -> String:
    var polygon := PackedVector2Array()
    for point in points:
        polygon.append(Vector2(float(point[0]) - offset_x, float(point[1]) - offset_y))
    return _packed_vector2_array(polygon)


static func _packed_vector2_array_scaled(polygon: PackedVector2Array, pixels_per_unit: float) -> String:
    var values := PackedStringArray()
    for point in polygon:
        values.append(_number(point.x / pixels_per_unit))
        values.append(_number(point.y / pixels_per_unit))
    return "PackedVector2Array(" + ", ".join(values) + ")"

static func _packed_vector2_array(polygon: PackedVector2Array) -> String:
    var values := PackedStringArray()
    for point in polygon:
        values.append(_number(point.x))
        values.append(_number(point.y))
    return "PackedVector2Array(" + ", ".join(values) + ")"


static func _number(value: float) -> String:
    if is_equal_approx(value, round(value)):
        return str(int(round(value)))
    return "%.9f" % value


static func _quote(value: String) -> String:
    return JSON.stringify(value)


static func _image_reference_from_manifest(payload: Dictionary) -> String:
    var source = payload.get("source")
    var image = source.get("image") if typeof(source) == TYPE_DICTIONARY else null
    return image.get("path", "") if typeof(image) == TYPE_DICTIONARY else ""


static func _collision_polygons(
    collision: Dictionary,
    rect_x: float,
    rect_y: float,
    pivot_x: float,
    pivot_y: float,
) -> Array:
    var point_sets: Array = []
    if collision.get("shape_type") == "compound" and typeof(collision.get("parts")) == TYPE_ARRAY:
        point_sets = collision.get("parts")
    else:
        point_sets = [collision.get("points", [])]
    var polygons: Array = []
    for points in point_sets:
        if typeof(points) != TYPE_ARRAY or points.size() < 3:
            continue
        var polygon := PackedVector2Array()
        for point in points:
            if typeof(point) != TYPE_ARRAY or point.size() != 2:
                polygon = PackedVector2Array()
                break
            polygon.append(Vector2(
                float(point[0]) - rect_x - pivot_x,
                float(point[1]) - rect_y - pivot_y
            ))
        if polygon.size() >= 3:
            polygons.append(polygon)
    return polygons


static func _is_project_relative(path: String) -> bool:
    return typeof(path) == TYPE_STRING and path.begins_with("res://") and not path.contains("..")


static func _is_safe_name(value: String) -> bool:
    return not value.contains("/") and not value.contains("\\") and not value.contains("..") and not value.contains(":")


static func _failure(manifest_path: String, message: String) -> Dictionary:
    return {"status": "FAILED", "manifest_path": manifest_path, "errors": [message]}
