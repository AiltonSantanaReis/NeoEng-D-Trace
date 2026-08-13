extends SceneTree


func fail(message: String) -> void:
    push_error(message)
    quit(1)


func _initialize() -> void:
    var handle := FileAccess.open("res://probe-godot.json", FileAccess.READ)
    if handle == null:
        fail("metadata-open")
        return
    var metadata = JSON.parse_string(handle.get_as_text())
    if typeof(metadata) != TYPE_DICTIONARY:
        fail("metadata-json")
        return
    if metadata.has("sprites"):
        var sprites = metadata.get("sprites")
        if typeof(sprites) != TYPE_ARRAY or sprites.size() != 1:
            fail("metadata-scene-wrapper")
            return
        metadata = sprites[0]
    if metadata.get("schema") != "neoeng-d-trace-godot-sprite":
        fail("metadata-schema")
        return
    if metadata.get("schema_version") != 1:
        fail("metadata-version")
        return
    if metadata.get("name") != "sprite_ação":
        fail("metadata-unicode-name")
        return
    var rect = metadata.get("rect", {})
    var texture = load("res://source.png")
    if not texture is Texture2D:
        fail("texture-import")
        return
    var atlas := AtlasTexture.new()
    atlas.atlas = texture
    atlas.region = Rect2(rect.x, rect.y, rect.w, rect.h)
    if atlas.get_size() != Vector2(40.0, 20.0):
        fail("atlas-region")
        return
    var sprite := Sprite2D.new()
    sprite.texture = atlas
    sprite.centered = true
    var offset = metadata.get("offset", {})
    sprite.offset = Vector2(offset.x, offset.y)
    if sprite.offset != Vector2.ZERO:
        fail("sprite-offset")
        return
    var collision = metadata.get("collision")
    if typeof(collision) != TYPE_DICTIONARY or collision.get("shape_type") != "polygon":
        fail("collision-schema")
        return
    var imported = load("res://scene.glb")
    if not imported is PackedScene:
        fail("glb-import")
        return
    var instance = imported.instantiate()
    if instance == null or instance.get_child_count() == 0:
        fail("glb-instance")
        return
    instance.free()
    sprite.free()
    atlas = null
    texture = null
    imported = null
    await process_frame
    print("ENGINE_VALIDATION=SUCCESS")
    print("ENGINE_VERSION=" + Engine.get_version_info().string)
    quit(0)
