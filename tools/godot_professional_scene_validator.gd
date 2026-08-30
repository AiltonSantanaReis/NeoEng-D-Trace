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
        print("P2D04_GODOT_DIAGNOSIS=" + JSON.stringify(diagnostic))
        fail("godot-export-diagnosis")
        return
    var imported := Importer.import_scene("res://scene.godot.runtime.json")
    if not require(imported.get("status") == "SUCCESS", "godot-import"):
        return
    var root: Node2D = imported["root"]
    get_root().add_child(root)
    await process_frame
    var camera := root.find_child("SceneCamera", true, false) as Camera2D
    if not require(camera != null, "godot-camera-materialization"):
        return
    if not require(camera.position.is_equal_approx(Vector2(0.8, 0.4)), "godot-camera-position"):
        return
    if not require(camera.zoom.is_equal_approx(Vector2(1.25, 1.25)), "godot-camera-zoom"):
        return
    camera.make_current()
    var parallax := root.find_child("Parallax_foreground", true, false) as Parallax2D
    if not require(parallax != null, "godot-parallax-materialization"):
        return
    if not require(parallax.scroll_scale.is_equal_approx(Vector2(0.82, 0.82)), "godot-parallax-scale"):
        return
    var sprite := root.find_child("Object_hero", true, false) as Sprite2D
    if not require(sprite != null, "godot-object-materialization"):
        return
    if not require(sprite.position.is_equal_approx(Vector2(0.8, 0.4)), "godot-object-position"):
        return
    if not require(is_equal_approx(sprite.rotation_degrees, 17.0), "godot-object-rotation"):
        return
    if not require(sprite.scale.is_equal_approx(Vector2(-1.2, 0.75)), "godot-object-scale-flip"):
        return
    if not require(sprite.offset.is_equal_approx(Vector2(19.2, -9.6)), "godot-object-pivot"):
        return
    await process_frame
    await process_frame
    var rendered := get_root().get_viewport().get_texture().get_image()
    if not require(not rendered.is_empty(), "godot-render-empty"):
        return
    var visible_pixels := 0
    for y in range(0, rendered.get_height(), 4):
        for x in range(0, rendered.get_width(), 4):
            if rendered.get_pixel(x, y).a > 0.05:
                visible_pixels += 1
    if not require(visible_pixels > 0, "godot-render-no-visible-pixels"):
        return
    rendered.save_png("res://godot-professional-capture.png")
    print("P2D04_GODOT_VALIDATION=SUCCESS")
    print("P2D04_GODOT_RENDER_PIXELS=" + str(visible_pixels))
    print("P2D04_GODOT_VERSION=" + Engine.get_version_info().string)
    quit(0)
