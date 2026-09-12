class_name NeoEngDTraceTilemapRuntime
extends RefCounted

## Runtime materialization of the authored sparse tilemap contract.
##
## The importer validates the source/atlas bindings before creating any
## Sprite2D.  A changed atlas therefore fails closed instead of rendering a
## visually plausible but incorrect scene.

const FORMAT_ID := "neoeng-d-trace-tilemap-runtime"
const SCHEMA_VERSION := 1


static func diagnose_tilemap(payload_path: String) -> Dictionary:
	var result := {"status": "FAILED", "errors": []}
	if not _is_project_relative(payload_path) or not FileAccess.file_exists(payload_path):
		result["errors"].append("tilemap runtime payload must be an existing res:// file")
		return result
	var payload = JSON.parse_string(FileAccess.get_file_as_string(payload_path))
	if typeof(payload) != TYPE_DICTIONARY:
		result["errors"].append("tilemap runtime payload JSON must be an object")
		return result
	_validate_payload(payload, payload_path.get_base_dir(), result["errors"])
	if result["errors"].is_empty():
		result["status"] = "SUCCESS"
		result.erase("errors")
	return result


static func import_tilemap(payload_path: String) -> Dictionary:
	var diagnostic := diagnose_tilemap(payload_path)
	if diagnostic.get("status") != "SUCCESS":
		return diagnostic
	var payload: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(payload_path))
	var base_dir := payload_path.get_base_dir()
	var atlas_path := base_dir.path_join(str(payload["atlas"]["path"]))
	var atlas_image := Image.new()
	if atlas_image.load(atlas_path) != OK:
		return {"status": "FAILED", "errors": ["tilemap atlas could not be loaded"]}
	var atlas: Texture2D = ImageTexture.create_from_image(atlas_image)

	var tile_lookup := {}
	for tile_value in payload["tileset"]["tiles"]:
		var tile: Dictionary = tile_value
		tile_lookup[str(tile["id"])] = tile
	var root := Node2D.new()
	root.name = "NeoEngRuntimeTilemap"
	root.set_meta("neoeng_tilemap_engine", "godot")
	root.set_meta("neoeng_tilemap_id", str(payload["id"]))
	root.set_meta("neoeng_tilemap_grid", str(payload["grid"]))
	root.set_meta("neoeng_tilemap_atlas_sha256", str(payload["atlas"]["sha256"]))
	root.set_meta("neoeng_tilemap_rule_count", int(payload["counts"]["rules"]))
	var layer_lookup := {}
	for layer_value in payload["layers"]:
		var layer_data: Dictionary = layer_value
		var layer := Node2D.new()
		layer.name = "TileLayer_%s" % str(layer_data["id"])
		layer.visible = bool(layer_data["visible"])
		layer.z_index = int(layer_data["order"])
		layer.modulate.a = float(layer_data["opacity"])
		layer.set_meta("neoeng_tile_layer_id", str(layer_data["id"]))
		root.add_child(layer)
		layer_lookup[str(layer_data["id"])] = layer

	var rendered_sprites := 0
	for cell_value in payload["cells"]:
		var cell: Dictionary = cell_value
		var tile: Dictionary = tile_lookup[str(cell["tile_id"])]
		var layer: Node2D = layer_lookup[str(cell["layer_id"])]
		var sprite := Sprite2D.new()
		sprite.name = "Tile_%s_%d_%d" % [str(cell["tile_id"]), int(cell["x"]), int(cell["y"])]
		sprite.texture = atlas
		sprite.region_enabled = true
		var rect: Dictionary = tile["source_rect"]
		sprite.region_rect = Rect2(float(rect["x"]), float(rect["y"]), float(rect["w"]), float(rect["h"]))
		sprite.centered = false
		sprite.position = _cell_position(payload, cell, rect)
		sprite.set_meta("neoeng_tile_id", str(cell["tile_id"]))
		layer.add_child(sprite)
		rendered_sprites += 1

	return {
		"status": "SUCCESS",
		"root": root,
		"engine": "godot",
		"tilemap_id": str(payload["id"]),
		"layers": int(payload["counts"]["layers"]),
		"tiles": int(payload["counts"]["tiles"]),
		"tile_cells": int(payload["counts"]["cells"]),
		"rendered_sprites": rendered_sprites,
		"rules": int(payload["counts"]["rules"]),
		"atlas_path": atlas_path,
		"atlas_sha256": str(payload["atlas"]["sha256"]),
	}


static func _cell_position(payload: Dictionary, cell: Dictionary, rect: Dictionary) -> Vector2:
	var x := float(cell["x"])
	var y := float(cell["y"])
	var width := float(rect["w"])
	var height := float(rect["h"])
	match str(payload["grid"]):
		"isometric":
			return Vector2((x - y) * width * 0.5, (x + y) * height * 0.5)
		"hexagonal":
			return Vector2(x * width * 0.75, y * height + fmod(abs(x), 2.0) * height * 0.5)
		_:
			return Vector2(x * width, y * height)


static func _validate_payload(payload: Dictionary, base_dir: String, errors: Array) -> void:
	for key in ["format_id", "schema_version", "source", "id", "name", "grid", "chunk_size", "tileset", "atlas", "layers", "cells", "rules", "counts"]:
		if not payload.has(key):
			errors.append("tilemap runtime payload is missing " + key)
	if not errors.is_empty():
		return
	if payload["format_id"] != FORMAT_ID or int(payload["schema_version"]) != SCHEMA_VERSION:
		errors.append("unsupported tilemap runtime format or schema")
	if str(payload["grid"]) not in ["orthogonal", "isometric", "hexagonal"]:
		errors.append("tilemap runtime grid is invalid")
	_validate_file_binding(payload["source"], base_dir, "source", errors)
	_validate_file_binding(payload["atlas"], base_dir, "atlas", errors)
	var tileset: Variant = payload["tileset"]
	if typeof(tileset) != TYPE_DICTIONARY or not tileset.has("atlas_sha256") or not tileset.has("tiles"):
		errors.append("tilemap runtime tileset is invalid")
		return
	if str(tileset["atlas_sha256"]) != str(payload["atlas"]["sha256"]):
		errors.append("tilemap runtime tileset and atlas hashes differ")
	var tile_ids := {}
	var tiles: Variant = tileset["tiles"]
	if typeof(tiles) != TYPE_ARRAY or tiles.is_empty():
		errors.append("tilemap runtime tileset has no tiles")
	else:
		for tile_value in tiles:
			if typeof(tile_value) != TYPE_DICTIONARY or not tile_value.has("id") or not tile_value.has("source_rect"):
				errors.append("tilemap runtime tile record is invalid")
				continue
			var tile: Dictionary = tile_value
			var tile_id := str(tile["id"])
			if tile_id.is_empty() or tile_ids.has(tile_id):
				errors.append("tilemap runtime tile IDs are invalid")
			tile_ids[tile_id] = true
			_validate_rect(tile["source_rect"], "tile", errors)

	var layer_ids := {}
	var layers: Variant = payload["layers"]
	if typeof(layers) != TYPE_ARRAY or layers.is_empty():
		errors.append("tilemap runtime has no layers")
	else:
		for layer_value in layers:
			if typeof(layer_value) != TYPE_DICTIONARY or not layer_value.has("id"):
				errors.append("tilemap runtime layer record is invalid")
				continue
			var layer: Dictionary = layer_value
			var layer_id := str(layer["id"])
			if layer_id.is_empty() or layer_ids.has(layer_id):
				errors.append("tilemap runtime layer IDs are invalid")
			layer_ids[layer_id] = true

	var cell_keys := {}
	var cells: Variant = payload["cells"]
	if typeof(cells) != TYPE_ARRAY:
		errors.append("tilemap runtime cells are invalid")
	else:
		for cell_value in cells:
			if typeof(cell_value) != TYPE_DICTIONARY:
				errors.append("tilemap runtime cell record is invalid")
				continue
			var cell: Dictionary = cell_value
			var layer_id := str(cell.get("layer_id", ""))
			var tile_id := str(cell.get("tile_id", ""))
			var key := "%s:%d:%d" % [layer_id, int(cell.get("x", 0)), int(cell.get("y", 0))]
			if not layer_ids.has(layer_id) or not tile_ids.has(tile_id) or cell_keys.has(key):
				errors.append("tilemap runtime cell references are invalid")
			cell_keys[key] = true

	var rules: Variant = payload["rules"]
	if typeof(rules) != TYPE_DICTIONARY or not rules.has("fallback_tile_id") or not tile_ids.has(str(rules["fallback_tile_id"])) or typeof(rules.get("rules", null)) != TYPE_ARRAY:
		errors.append("tilemap runtime rules are invalid")
	var counts: Variant = payload["counts"]
	if typeof(counts) != TYPE_DICTIONARY or int(counts.get("layers", -1)) != layers.size() or int(counts.get("tiles", -1)) != tiles.size() or int(counts.get("cells", -1)) != cells.size() or int(counts.get("rules", -1)) != rules.get("rules", []).size():
		errors.append("tilemap runtime counts are inconsistent")


static func _validate_rect(value: Variant, label: String, errors: Array) -> void:
	if typeof(value) != TYPE_DICTIONARY:
		errors.append(label + " source rectangle is invalid")
		return
	for key in ["x", "y", "w", "h"]:
		if not value.has(key) or not is_finite(float(value[key])):
			errors.append(label + " source rectangle is invalid")
	if int(value.get("x", -1)) < 0 or int(value.get("y", -1)) < 0 or int(value.get("w", 0)) <= 0 or int(value.get("h", 0)) <= 0:
		errors.append(label + " source rectangle has invalid bounds")


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


static func _safe_relative_path(path: String) -> bool:
	if path.is_empty() or path.begins_with("/") or path.contains("\\") or path.contains(":"):
		return false
	for part in path.split("/"):
		if part.is_empty() or part == "." or part == "..":
			return false
	return true


static func _is_project_relative(path: String) -> bool:
	return path.begins_with("res://") and not path.contains("..")


static func _sha256_bytes(bytes: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(bytes)
	return context.finish().hex_encode()
