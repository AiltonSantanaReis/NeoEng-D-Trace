extends SceneTree

const Importer = preload("res://addons/neoeng_d_trace/scenario_importer.gd")


func _fail(message: String) -> void:
    push_error(message)
    quit(1)


func _check(condition: bool, message: String) -> bool:
    if not condition:
        _fail(message)
        return false
    return true


func _initialize() -> void:
    var export_path := OS.get_environment("NEOENG_SCENARIO_EXPORT")
    if export_path.is_empty():
        export_path = "res://NeoEngGenerated/scenario.ndtscenario.runtime.json"
    var result := Importer.import_scenario(export_path)
    if not _check(result.get("status") == "SUCCESS", "scenario-import:" + JSON.stringify(result)):
        return
    var root: Node2D = result["root"]
    if not _check(root.get_child_count() == 2, "scenario-layer-count"):
        return
    if not _check(root.get_meta("neoeng_camera_position") == Vector2(12.0, -4.0), "scenario-camera-position"):
        return
    if not _check(is_equal_approx(float(root.get_meta("neoeng_camera_zoom")), 1.5), "scenario-camera-zoom"):
        return
    var first := root.get_child(0) as Node2D
    var second := root.get_child(1) as Node2D
    if not _check(first != null and second != null, "scenario-layer-nodes"):
        return
    if not _check(first.get_meta("neoeng_layer_id") == "layer_foreground", "scenario-layer-id"):
        return
    if not _check(first.visible and not second.visible, "scenario-layer-visibility"):
        return
    if not _check(first.get_meta("neoeng_object_ids") == PackedStringArray(["object_a"]), "scenario-object-references"):
        return
    if not _check(is_equal_approx(float(first.get_meta("neoeng_parallax_depth")), 0.25), "scenario-parallax-depth"):
        return
    if not _check(is_equal_approx(float(second.get_meta("neoeng_parallax_zoom_strength")), 0.4), "scenario-parallax-zoom"):
        return
    root.free()
    print("SCENARIO_ENGINE_STAGE4B4=SUCCESS")
    print("SCENARIO_LAYERS=2")
    print("SCENARIO_OBJECT_REFERENCES=1")
    print("SCENARIO_METADATA_ONLY=true")
    print("SCENARIO_PARALLAX_VALUES_PRESERVED=true")
    quit(0)
