class_name NeoEngDTraceHybrid3DRuntime
extends RefCounted

## Runtime materialization of the bounded hybrid 3D vertical slice.
##
## The adapter consumes only the hash-bound hybrid-runtime.json contract. It
## validates every referenced file before creating a Node3D, then creates real
## MeshInstance3D, Camera3D, Light3D and AnimationPlayer nodes. It does not
## claim collision, particles, tilemap 3D or the complete 3D product.

const FORMAT_ID := "neoeng-d-trace-hybrid-runtime"
const SCHEMA_VERSION := 1
const SCENE_FORMAT_ID := "neoeng-d-trace-hybrid-runtime-scene"
const SCENE_SCHEMA_VERSION := 1


static func diagnose_hybrid(runtime_manifest_path: String) -> Dictionary:
	var result := {"status": "FAILED", "errors": []}
	if not _is_project_relative(runtime_manifest_path) or not FileAccess.file_exists(runtime_manifest_path):
		result["errors"].append("hybrid runtime manifest must be an existing res:// file")
		return result
	var payload = JSON.parse_string(FileAccess.get_file_as_string(runtime_manifest_path))
	if typeof(payload) != TYPE_DICTIONARY:
		result["errors"].append("hybrid runtime manifest JSON must be an object")
		return result
	_validate_payload(payload, runtime_manifest_path.get_base_dir(), result["errors"])
	if result["errors"].is_empty():
		result["status"] = "SUCCESS"
		result.erase("errors")
	return result


static func import_hybrid(runtime_manifest_path: String) -> Dictionary:
	var diagnostic := diagnose_hybrid(runtime_manifest_path)
	if diagnostic.get("status") != "SUCCESS":
		return diagnostic
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(runtime_manifest_path))
	var base_dir := runtime_manifest_path.get_base_dir()
	var scene_path := base_dir.path_join(str(manifest["scene"]["normalized"]["path"]))
	var scene: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(scene_path))
	var animation_path := base_dir.path_join(str(manifest["animation"]["manifest"]["path"]))
	var animation_manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(animation_path))
	var first_frame_path := base_dir.path_join(str(manifest["animation"]["first_frame"]["path"]))
	var first_frame := Image.new()
	if first_frame.load(first_frame_path) != OK:
		return {"status": "FAILED", "errors": ["hybrid animation first frame could not be decoded"]}

	var root := Node3D.new()
	root.name = "NeoEngRuntimeHybrid3D"
	root.set_meta("neoeng_hybrid_engine", "godot")
	root.set_meta("neoeng_hybrid_support_status", str(manifest["support_status"]))
	root.set_meta("neoeng_hybrid_runtime_manifest", runtime_manifest_path)
	root.set_meta("neoeng_hybrid_source_path", str(manifest["scene"]["authoring"]["path"]))
	root.set_meta("neoeng_hybrid_animation_frame_count", int(manifest["animation"]["frame_count"]))

	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.035, 0.055, 0.09, 1.0)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.35, 0.45, 0.65, 1.0)
	environment.ambient_light_energy = 0.55
	var world := WorldEnvironment.new()
	world.environment = environment
	root.add_child(world)

	var camera_data: Dictionary = scene["camera"]
	var camera := Camera3D.new()
	camera.name = "PerspectiveCamera"
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	camera.fov = float(camera_data["fov_degrees"])
	camera.near = float(camera_data["near"])
	camera.far = float(camera_data["far"])
	camera.position = _point(camera_data["position"])
	root.add_child(camera)
	camera.look_at_from_position(camera.position, _point(camera_data["target"]))
	camera.current = true

	var material_by_id := {}
	for material_value in scene["materials"]:
		var material_data: Dictionary = material_value
		var material := StandardMaterial3D.new()
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		var color_values: Array = material_data.get("base_color", [0.15, 0.72, 0.95, 1.0])
		material.albedo_color = Color(float(color_values[0]), float(color_values[1]), float(color_values[2]), float(color_values[3]))
		material.metallic = float(material_data["metallic"])
		material.roughness = float(material_data["roughness"])
		material_by_id[str(material_data["id"])] = material

	var mesh_nodes := {}
	for mesh_value in scene["meshes"]:
		var mesh_data: Dictionary = mesh_value
		var vertices := PackedVector3Array()
		for vertex_value in mesh_data["vertices"]:
			vertices.append(_point(vertex_value))
		var indices := PackedInt32Array()
		for triangle_value in mesh_data["triangles"]:
			var triangle: Dictionary = triangle_value
			indices.append(int(triangle["a"]))
			indices.append(int(triangle["b"]))
			indices.append(int(triangle["c"]))
		var arrays: Array = []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = vertices
		arrays[Mesh.ARRAY_INDEX] = indices
		var array_mesh := ArrayMesh.new()
		array_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var mesh_node := MeshInstance3D.new()
		mesh_node.name = str(mesh_data["id"])
		mesh_node.mesh = array_mesh
		mesh_node.position = _point(mesh_data["position"])
		mesh_node.set_surface_override_material(0, material_by_id[str(mesh_data["material_id"])])
		root.add_child(mesh_node)
		mesh_nodes[mesh_node.name] = mesh_node

	for light_value in scene["lights"]:
		var light_data: Dictionary = light_value
		var light: Light3D
		if str(light_data["type"]) == "point":
			light = OmniLight3D.new()
		else:
			light = DirectionalLight3D.new()
		light.name = str(light_data["id"])
		light.light_energy = float(light_data["intensity"])
		light.position = _point(light_data["position"])
		root.add_child(light)
		if light is DirectionalLight3D:
			light.look_at_from_position(light.position, Vector3.ZERO)

	var player := AnimationPlayer.new()
	player.name = "HybridAnimationPlayer"
	player.root_node = NodePath("..")
	var library := AnimationLibrary.new()
	for clip_value in scene["animation_clips"]:
		var clip_data: Dictionary = clip_value
		var clip := Animation.new()
		var track := clip.add_track(Animation.TYPE_POSITION_3D)
		clip.track_set_path(track, NodePath(str(clip_data["mesh_id"]) + ":position"))
		for keyframe_value in clip_data["keyframes"]:
			var keyframe: Dictionary = keyframe_value
			clip.track_insert_key(track, float(keyframe["time"]), _point(keyframe["position"]))
		clip.length = float(clip_data["keyframes"][-1]["time"])
		library.add_animation(str(clip_data["id"]), clip)
	player.add_animation_library("", library)
	root.add_child(player)
	var first_clip: Dictionary = scene["animation_clips"][0]
	player.play(str(first_clip["id"]))
	player.advance(float(first_clip["keyframes"][-1]["time"]) * 0.5)
	var animated_mesh: Node3D = mesh_nodes[str(first_clip["mesh_id"])]
	if not is_finite(animated_mesh.position.y):
		return {"status": "FAILED", "errors": ["hybrid animation playback produced a non-finite position"]}

	return {
		"status": "SUCCESS",
		"root": root,
		"camera": camera,
		"engine": "godot",
		"support_status": str(manifest["support_status"]),
		"mesh_count": scene["meshes"].size(),
		"material_count": scene["materials"].size(),
		"light_count": scene["lights"].size(),
		"animation_clip_count": scene["animation_clips"].size(),
		"animation_frame_count": int(animation_manifest["frame_count"]),
		"animation_frame_loaded": true,
		"animation_frame_size": [first_frame.get_width(), first_frame.get_height()],
		"animation_playback": true,
		"playback_position_y": animated_mesh.position.y,
	}


static func _validate_payload(payload: Dictionary, base_dir: String, errors: Array) -> void:
	if payload.get("format_id") != FORMAT_ID or int(payload.get("schema_version", -1)) != SCHEMA_VERSION:
		errors.append("unsupported hybrid runtime manifest")
	if payload.get("support_status") != "VERTICAL_SLICE_ONLY":
		errors.append("hybrid runtime support status is not explicit")
	var scene: Variant = payload.get("scene")
	if typeof(scene) != TYPE_DICTIONARY:
		errors.append("hybrid runtime scene bindings are missing")
	else:
		_validate_binding(scene.get("authoring"), base_dir, "scene.authoring", errors)
		_validate_binding(scene.get("normalized"), base_dir, "scene.normalized", errors)
		var normalized_path := base_dir.path_join(str(scene.get("normalized", {}).get("path", "")))
		if FileAccess.file_exists(normalized_path):
			var normalized = JSON.parse_string(FileAccess.get_file_as_string(normalized_path))
			_validate_scene(normalized, errors)
	var animation: Variant = payload.get("animation")
	if typeof(animation) != TYPE_DICTIONARY:
		errors.append("hybrid runtime animation bindings are missing")
	else:
		_validate_binding(animation.get("manifest"), base_dir, "animation.manifest", errors)
		_validate_binding(animation.get("first_frame"), base_dir, "animation.first_frame", errors)
		var animation_path := base_dir.path_join(str(animation.get("manifest", {}).get("path", "")))
		if FileAccess.file_exists(animation_path):
			var animation_manifest = JSON.parse_string(FileAccess.get_file_as_string(animation_path))
			if typeof(animation_manifest) != TYPE_DICTIONARY or animation_manifest.get("frame_count") != int(animation.get("frame_count", -1)):
				errors.append("hybrid runtime animation frame count is inconsistent")


static func _validate_scene(scene: Variant, errors: Array) -> void:
	if typeof(scene) != TYPE_DICTIONARY:
		errors.append("hybrid runtime scene JSON must be an object")
		return
	if scene.get("format_id") != SCENE_FORMAT_ID or int(scene.get("schema_version", -1)) != SCENE_SCHEMA_VERSION:
		errors.append("unsupported hybrid runtime scene")
	if scene.get("support_status") != "VERTICAL_SLICE_ONLY":
		errors.append("hybrid runtime scene support status is not explicit")
	for key in ["camera", "materials", "meshes", "lights", "animation_clips"]:
		if not scene.has(key):
			errors.append("hybrid runtime scene is missing " + key)
	if typeof(scene.get("camera")) == TYPE_DICTIONARY and scene["camera"].get("projection") != "perspective":
		errors.append("hybrid runtime camera projection is unsupported")
	if typeof(scene.get("materials")) != TYPE_ARRAY or scene["materials"].is_empty():
		errors.append("hybrid runtime scene has no materials")
	if typeof(scene.get("meshes")) != TYPE_ARRAY or scene["meshes"].is_empty():
		errors.append("hybrid runtime scene has no meshes")
	if typeof(scene.get("lights")) != TYPE_ARRAY or scene["lights"].is_empty():
		errors.append("hybrid runtime scene has no lights")
	if typeof(scene.get("animation_clips")) != TYPE_ARRAY or scene["animation_clips"].is_empty():
		errors.append("hybrid runtime scene has no animation clips")


static func _validate_binding(binding: Variant, base_dir: String, label: String, errors: Array) -> void:
	if typeof(binding) != TYPE_DICTIONARY or not binding.has("path") or not binding.has("sha256") or not binding.has("bytes"):
		errors.append(label + " binding is incomplete")
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
		errors.append(label + " file hash mismatch or size mismatch")


static func _point(value: Dictionary) -> Vector3:
	return Vector3(float(value.get("x", 0.0)), float(value.get("y", 0.0)), float(value.get("z", 0.0)))


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
