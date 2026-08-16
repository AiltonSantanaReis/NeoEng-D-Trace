@tool
extends Node2D

var _animated_sprite: AnimatedSprite2D


func _ready() -> void:
    _animated_sprite = get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
    if _animated_sprite == null:
        return
    _animated_sprite.frame_changed.connect(_sync_collision_state)
    _animated_sprite.animation_changed.connect(_sync_collision_state)
    _sync_collision_state()


func _exit_tree() -> void:
    if _animated_sprite == null:
        return
    if _animated_sprite.frame_changed.is_connected(_sync_collision_state):
        _animated_sprite.frame_changed.disconnect(_sync_collision_state)
    if _animated_sprite.animation_changed.is_connected(_sync_collision_state):
        _animated_sprite.animation_changed.disconnect(_sync_collision_state)


func _sync_collision_state() -> void:
    var animated_sprite := get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
    if animated_sprite == null:
        return
    var active_frame := animated_sprite.frame
    for child in get_children():
        if not child is CollisionPolygon2D:
            continue
        var collision := child as CollisionPolygon2D
        if not collision.name.begins_with("AnimationCollision_"):
            continue
        var frame_text := collision.name.trim_prefix("AnimationCollision_")
        collision.disabled = int(frame_text) != active_frame