extends SceneTree

const IMPORTER = preload("res://addons/neoeng_d_trace/professional_scene_importer.gd")


func _initialize() -> void:
    var export_path := "res://NeoEngGenerated/scene-authoring.godot.json"
    var diagnostic: Dictionary = IMPORTER.diagnose_export(export_path)
    if diagnostic.get("status") != "SUCCESS":
        push_error("GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE:" + JSON.stringify(diagnostic))
        quit(1)
        return
    var imported: Dictionary = IMPORTER.import_scene(export_path)
    if imported.get("status") != "SUCCESS":
        push_error("GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE:" + JSON.stringify(imported))
        quit(1)
        return
    var root: Node2D = imported["root"]
    _require(root.name == "NeoEngProfessionalScene", "root-name")
    _require(root.get_child_count() == 1, "layer-count")
    var layer: Node2D = root.get_child(0)
    _require(layer.get_meta("neoeng_layer_id") == "foreground", "layer-id")
    _require(layer.get_child_count() == 2, "layer-content-count")
    var sprite: Sprite2D = layer.get_node("Object_hero")
    _require(sprite.position == Vector2(10.0, 20.0), "object-position")
    _require(sprite.z_index == 3, "object-depth")
    _require(sprite.rotation_degrees == 15.0, "object-rotation")
    _require(sprite.scale.x == -1.0, "object-flip")
    _require(sprite.get_meta("neoeng_pivot") == {"x": 0.5, "y": 1.0}, "object-pivot")
    var socket: Node2D = layer.get_node("Socket_lamp")
    _require(socket.get_meta("neoeng_socket_type") == "light", "socket-type")
    var object_count := 0
    for child in layer.get_children():
        if child is Sprite2D:
            object_count += 1
    print("GODOT_PROFESSIONAL_SCENE_LAYERS=" + str(root.get_child_count()))
    print("GODOT_PROFESSIONAL_SCENE_OBJECTS=" + str(object_count))
    print("GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS")
    root.queue_free()
    quit(0)


func _require(condition: bool, label: String) -> void:
    if not condition:
        push_error("GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE:" + label)
        quit(1)
