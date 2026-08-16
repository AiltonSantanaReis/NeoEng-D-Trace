extends SceneTree

const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")


func _fail(message: String) -> void:
    push_error(message)
    quit(1)


func _check(condition: bool, message: String) -> bool:
    if not condition:
        _fail(message)
        return false
    return true


func _write_variant_manifest(object_id: String, filename: String) -> String:
    var payload = JSON.parse_string(FileAccess.get_file_as_string("res://NeoEngGenerated/hero.ndt.integration.json"))
    payload["metadata"]["sprites"][0]["id"] = object_id
    var path := "res://NeoEngGenerated/" + filename
    var file := FileAccess.open(path, FileAccess.WRITE)
    file.store_string(JSON.stringify(payload, "  "))
    file.close()
    return path


func _initialize() -> void:
    var first := Importer.import_manifest("res://NeoEngGenerated/hero.ndt.integration.json")
    if not _check(first.get("status") == "SUCCESS", "import:" + JSON.stringify(first)):
        return

    var project_import := Importer.import_project("res://NeoEngGenerated")
    if not _check(project_import.get("status") == "SUCCESS", "project-import:" + JSON.stringify(project_import)):
        return

    var scene_path := "res://NeoEngGenerated/hero.tscn"
    if not _check(FileAccess.file_exists(scene_path), "generated-scene-missing"):
        return
    var packed := load(scene_path) as PackedScene
    if not _check(packed != null, "generated-scene-load"):
        return
    var instance := packed.instantiate()
    if not _check(instance != null, "generated-scene-instantiate"):
        return
    var sprite := instance.get_node_or_null("Sprite2D") as Sprite2D
    if not _check(sprite != null and sprite.texture is AtlasTexture, "sprite-atlas"):
        return
    var atlas := sprite.texture as AtlasTexture
    if not _check(atlas.region == Rect2(0.0, 0.0, 16.0, 12.0), "sprite-region"):
        return
    if not _check(sprite.offset == Vector2(0.0, 0.0), "sprite-pivot-offset"):
        return
    var collision := instance.get_node_or_null("CollisionPolygon2D") as CollisionPolygon2D
    if not _check(collision != null and collision.polygon.size() == 4, "collision-polygon"):
        return
    if not _check(collision.polygon[0] == Vector2(-8.0, -6.0) and collision.polygon[2] == Vector2(8.0, 6.0), "collision-coordinate-conversion"):
        return
    if not _check(bool(instance.get_meta("neoeng_generated", false)), "generated-marker"):
        return
    if not _check(instance.get_meta("neoeng_layer") == "layer_default" and instance.get_meta("neoeng_group") == "", "sprite-properties"):
        return
    if not _check(instance.get_meta("neoeng_padding") == 4 and bool(instance.get_meta("neoeng_trimmed")), "sprite-properties-values"):
        return
    var collision_points := collision.polygon.size()
    var original_bytes := FileAccess.get_file_as_bytes(scene_path)
    instance.free()

    var compound_scene := load("res://NeoEngGenerated/compound.tscn") as PackedScene
    if not _check(compound_scene != null, "compound-scene-load"):
        return
    var compound_instance := compound_scene.instantiate()
    if not _check(compound_instance != null, "compound-scene-instantiate"):
        return
    var compound_polygons := compound_instance.get_children().filter(func(child): return child is CollisionPolygon2D)
    if not _check(compound_polygons.size() == 2, "compound-collision-polygon-count"):
        return
    compound_instance.free()

    var tileset := load("res://NeoEngGenerated/tileset.tres") as TileSet
    if not _check(tileset != null, "tileset-load"):
        return
    if not _check(tileset.tile_size == Vector2i(16, 12), "tileset-size"):
        return
    if not _check(tileset.get_source_count() == 1, "tileset-source-count"):
        return
    var atlas_source := tileset.get_source(0) as TileSetAtlasSource
    if not _check(atlas_source != null and atlas_source.has_tile(Vector2i(0, 0)) and atlas_source.has_tile(Vector2i(1, 0)), "tileset-atlas-tiles"):
        return
    var tile_data := atlas_source.get_tile_data(Vector2i(0, 0), 0)
    if not _check(tile_data != null and tile_data.get_collision_polygons_count(0) == 1, "tileset-collision"):
        return
    var tile_points := tile_data.get_collision_polygon_points(0, 0)
    if not _check(tile_points.size() == 4 and tile_points[0] == Vector2(0.0, 0.0), "tileset-collision-points"):
        return

    var animation_scene := load("res://NeoEngGenerated/animation.tscn") as PackedScene
    if not _check(animation_scene != null, "animation-scene-load"):
        return
    var animation_instance := animation_scene.instantiate()
    if not _check(animation_instance != null, "animation-scene-instantiate"):
        return
    var animated_sprite := animation_instance.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
    if not _check(animated_sprite != null and animated_sprite.sprite_frames.get_frame_count(&"default") == 2, "animation-frame-count"):
        return
    var animation_collision_0 := animation_instance.get_node_or_null("AnimationCollision_0") as CollisionPolygon2D
    var animation_collision_1 := animation_instance.get_node_or_null("AnimationCollision_1") as CollisionPolygon2D
    if not _check(animation_collision_0 != null and animation_collision_1 != null, "animation-collision-nodes"):
        return
    if not _check(not animation_collision_0.disabled and animation_collision_1.disabled, "animation-initial-collision-state"):
        return
    animated_sprite.frame = 1
    animation_instance.call("_sync_collision_state")
    if not _check(animation_collision_0.disabled and not animation_collision_1.disabled, "animation-frame-collision-sync"):
        return
    animation_instance.free()

    var second := Importer.import_manifest("res://NeoEngGenerated/hero.ndt.integration.json")
    if not _check(second.get("status") == "SUCCESS", "repeat-import:" + JSON.stringify(second)):
        return
    var repeated_bytes := FileAccess.get_file_as_bytes(scene_path)
    if not _check(original_bytes == repeated_bytes, "non-deterministic-generated-scene"):
        return

    var animation_conflict_manifest := _write_variant_manifest("animation_conflict", "animation-conflict.ndt.integration.json")
    var manual_animation := "res://NeoEngGenerated/animation.tscn"
    var generated_animation_bytes := FileAccess.get_file_as_bytes(manual_animation)
    var manual_animation_file := FileAccess.open(manual_animation, FileAccess.WRITE)
    manual_animation_file.store_string("[gd_scene format=3]\n\n[node name=\"ManualAnimation\" type=\"Node2D\"]\n")
    manual_animation_file.close()
    var animation_before := FileAccess.get_file_as_bytes(manual_animation)
    var animation_conflict := Importer.import_manifest(animation_conflict_manifest)
    if not _check(animation_conflict.get("status") == "CONFLICT", "animation-overwrite-not-blocked:" + JSON.stringify(animation_conflict)):
        return
    if not _check(animation_before == FileAccess.get_file_as_bytes(manual_animation), "animation-manual-mutated"):
        return
    var restored_animation := FileAccess.open(manual_animation, FileAccess.WRITE)
    restored_animation.store_buffer(generated_animation_bytes)
    restored_animation.close()

    var tileset_conflict_manifest := _write_variant_manifest("tileset_conflict", "tileset-conflict.ndt.integration.json")
    var manual_tileset := "res://NeoEngGenerated/tileset.tres"
    var generated_tileset_bytes := FileAccess.get_file_as_bytes(manual_tileset)
    var manual_tileset_file := FileAccess.open(manual_tileset, FileAccess.WRITE)
    manual_tileset_file.store_string("[gd_resource type=\"TileSet\" format=3]\n\n[resource]\n")
    manual_tileset_file.close()
    var tileset_before := FileAccess.get_file_as_bytes(manual_tileset)
    var tileset_conflict := Importer.import_manifest(tileset_conflict_manifest)
    if not _check(tileset_conflict.get("status") == "CONFLICT", "tileset-overwrite-not-blocked:" + JSON.stringify(tileset_conflict)):
        return
    if not _check(tileset_before == FileAccess.get_file_as_bytes(manual_tileset), "tileset-manual-mutated"):
        return
    var restored_tileset := FileAccess.open(manual_tileset, FileAccess.WRITE)
    restored_tileset.store_buffer(generated_tileset_bytes)
    restored_tileset.close()

    var manual_payload = JSON.parse_string(FileAccess.get_file_as_string("res://NeoEngGenerated/hero.ndt.integration.json"))
    manual_payload["metadata"]["sprites"][0]["id"] = "manual"
    var manual_manifest := "res://NeoEngGenerated/manual.ndt.integration.json"
    var manual_file := FileAccess.open(manual_manifest, FileAccess.WRITE)
    manual_file.store_string(JSON.stringify(manual_payload, "  "))
    manual_file.close()
    var manual_scene := "res://NeoEngGenerated/manual.tscn"
    var manual_scene_file := FileAccess.open(manual_scene, FileAccess.WRITE)
    manual_scene_file.store_string("[gd_scene format=3]\n\n[node name=\"Manual\" type=\"Node2D\"]\n")
    manual_scene_file.close()
    var manual_before := FileAccess.get_file_as_bytes(manual_scene)
    var conflict := Importer.import_manifest(manual_manifest)
    if not _check(conflict.get("status") == "CONFLICT", "manual-overwrite-not-blocked:" + JSON.stringify(conflict)):
        return
    if not _check(manual_before == FileAccess.get_file_as_bytes(manual_scene), "manual-scene-mutated"):
        return

    print("NATIVE_PLUGIN_STAGE4_CORE=SUCCESS")
    print("GENERATED_SCENE=" + scene_path)
    print("COLLISION_POINTS=" + str(collision_points))
    print("COMPOUND_COLLISION_POLYGONS=2")
    print("TILESET_NATIVE_LOADED=true")
    print("TILESET_COLLISION_POINTS=" + str(tile_points.size()))
    print("ANIMATION_FRAMES=2")
    print("ANIMATION_FRAME_COLLISION_SYNC=true")
    print("SPRITE_PROPERTIES_PRESERVED=true")
    print("REPEAT_IMPORT_DETERMINISTIC=true")
    print("MANUAL_OVERWRITE_BLOCKED=true")
    quit(0)
