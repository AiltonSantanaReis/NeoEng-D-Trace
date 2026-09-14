extends Node

const MODEL_PATH := "res://eclipse_warden.glb"
const CAPTURE_NAMES := ["preview_front.png", "preview_three_quarter.png", "preview_side.png", "preview_idle.png"]

var model: Node3D
var camera: Camera3D
var errors: Array[String] = []
var warnings: Array[String] = []
var animation_player: AnimationPlayer


func _ready() -> void:
	call_deferred("_run_capture")


func _run_capture() -> void:
	var report := {
		"status": "IN_PROGRESS",
		"engine": "Godot",
		"engine_version": Engine.get_version_info().get("string", "unknown"),
		"model_path": MODEL_PATH,
		"captures": [],
		"mesh_instance_count": 0,
		"surface_count": 0,
		"animation_players": 0,
		"errors": errors,
		"warnings": warnings,
	}
	var packed := load(MODEL_PATH)
	if packed == null or not (packed is PackedScene):
		errors.append("GLB could not be imported as a PackedScene")
		_finish(report)
		return
	model = packed.instantiate()
	model.name = "EclipseWardenImportedGLB"
	get_tree().root.add_child(model)
	_setup_world()
	await get_tree().process_frame
	await get_tree().process_frame
	var mesh_nodes := model.find_children("*", "MeshInstance3D", true, false)
	report["mesh_instance_count"] = mesh_nodes.size()
	for mesh_node in mesh_nodes:
		var mesh_instance := mesh_node as MeshInstance3D
		if mesh_instance.mesh != null:
			report["surface_count"] += mesh_instance.mesh.get_surface_count()
	animation_player = _find_animation_player(model)
	report["animation_players"] = 1 if animation_player != null else 0
	if animation_player == null:
		warnings.append("No AnimationPlayer was exposed by the Godot glTF importer")
	else:
		if not animation_player.has_animation("Idle"):
			errors.append("Imported AnimationPlayer does not expose Idle")
		else:
			animation_player.play("Idle")
	for capture_index in range(CAPTURE_NAMES.size()):
		var capture_name: String = CAPTURE_NAMES[capture_index]
		_set_camera(capture_index)
		await get_tree().process_frame
		await get_tree().process_frame
		var image := get_tree().root.get_viewport().get_texture().get_image()
		if image == null or image.is_empty():
			errors.append("Viewport image was empty for " + capture_name)
			continue
		var save_error := image.save_png("res://" + capture_name)
		if save_error != OK:
			errors.append("Could not save " + capture_name + " error=" + str(save_error))
		else:
			report["captures"].append(capture_name)
	report["warnings"] = warnings
	report["errors"] = errors
	report["imported_model_name"] = model.name
	report["status"] = "PASS" if errors.is_empty() and mesh_nodes.size() >= 10 else "FAIL"
	_write_report(report)
	get_tree().quit(0 if report["status"] == "PASS" else 2)


func _setup_world() -> void:
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.012, 0.022, 0.045, 1.0)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.23, 0.34, 0.58, 1.0)
	environment.ambient_light_energy = 0.72
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = environment
	get_tree().root.add_child(world)

	var key := DirectionalLight3D.new()
	key.name = "KeyLight"
	key.rotation_degrees = Vector3(-38.0, -32.0, 0.0)
	key.light_color = Color(0.78, 0.86, 1.0, 1.0)
	key.light_energy = 2.1
	key.shadow_enabled = true
	get_tree().root.add_child(key)

	var rim := OmniLight3D.new()
	rim.name = "BlueRimLight"
	rim.position = Vector3(-2.5, 3.2, -3.0)
	rim.light_color = Color(0.10, 0.32, 1.0, 1.0)
	rim.light_energy = 8.0
	rim.omni_range = 7.0
	get_tree().root.add_child(rim)

	var fill := OmniLight3D.new()
	fill.name = "WarmFillLight"
	fill.position = Vector3(3.5, 2.4, 3.0)
	fill.light_color = Color(1.0, 0.38, 0.16, 1.0)
	fill.light_energy = 4.5
	fill.omni_range = 6.0
	get_tree().root.add_child(fill)

	var ground := MeshInstance3D.new()
	ground.name = "PreviewGround"
	var plane := PlaneMesh.new()
	plane.size = Vector2(20.0, 20.0)
	ground.mesh = plane
	var ground_material := StandardMaterial3D.new()
	ground_material.albedo_color = Color(0.018, 0.024, 0.042, 1.0)
	ground_material.metallic = 0.35
	ground_material.roughness = 0.72
	ground.material_override = ground_material
	get_tree().root.add_child(ground)

	camera = Camera3D.new()
	camera.name = "ValidationCamera"
	camera.fov = 42.0
	camera.near = 0.05
	camera.far = 100.0
	camera.current = true
	get_tree().root.add_child(camera)


func _set_camera(capture_index: int) -> void:
	var positions := [
		Vector3(0.0, 2.55, 9.5),
		Vector3(5.7, 3.25, 7.2),
		Vector3(-8.7, 3.0, 0.25),
		Vector3(0.0, 2.65, 9.0),
	]
	camera.position = positions[capture_index]
	camera.look_at(Vector3(0.0, 2.25, 0.0), Vector3.UP)
	if capture_index == 3 and animation_player != null and animation_player.has_animation("Idle"):
		animation_player.seek(1.0, true)


func _find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node as AnimationPlayer
	for child in node.get_children():
		var found := _find_animation_player(child)
		if found != null:
			return found
	return null


func _write_report(report: Dictionary) -> void:
	var file := FileAccess.open("res://godot-runtime-report.json", FileAccess.WRITE)
	if file == null:
		errors.append("Could not open godot-runtime-report.json")
		return
	report["errors"] = errors
	report["warnings"] = warnings
	file.store_string(JSON.stringify(report, "\t"))
	file.close()


func _finish(report: Dictionary) -> void:
	report["errors"] = errors
	report["warnings"] = warnings
	report["status"] = "FAIL"
	_write_report(report)
	get_tree().quit(2)
