extends SceneTree

const Importer = preload("res://professional_scene_importer.gd")


func fail(message: String) -> void:
    push_error(message)
    quit(1)


func require(condition: bool, message: String) -> bool:
    if not condition:
        fail(message)
        return false
    return true


func _initialize() -> void:
    var diagnostic := Importer.diagnose_export("res://scene.godot.runtime.json")
    if diagnostic.get("status") != "SUCCESS":
        print("E10_GODOT_DIAGNOSIS=" + JSON.stringify(diagnostic))
    if not require(diagnostic.get("status") == "SUCCESS", "godot-vector-diagnosis"):
        return
    var imported := Importer.import_scene("res://scene.godot.runtime.json")
    if not require(imported.get("status") == "SUCCESS", "godot-vector-import"):
        return
    var root: Node2D = imported["root"]
    get_root().add_child(root)
    await process_frame
    var sprite := root.find_child("Object_subject-object", true, false) as Sprite2D
    if not require(sprite != null and sprite.texture != null, "godot-vector-sprite"):
        return
    var body := root.find_child("VectorCollision_subject-object", true, false) as StaticBody2D
    if not require(body != null, "godot-vector-collision-body"):
        return
    var collision := body.get_child(0) as CollisionPolygon2D
    if not require(collision != null and collision.polygon.size() == 4, "godot-vector-collision-polygon"):
        return
    print("E10_GODOT_VECTOR_VALIDATION=SUCCESS")
    print("E10_GODOT_VERSION=" + Engine.get_version_info().string)
    print("E10_GODOT_COLLISION_POINTS=" + str(collision.polygon.size()))
    quit(0)
