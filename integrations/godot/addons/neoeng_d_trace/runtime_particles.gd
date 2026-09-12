class_name NeoEngDTraceRuntimeParticles
extends Node2D

const UINT32_MASK := 0xffffffff
const UINT32_SCALE := 1.0 / 4294967296.0
const MAX_EMITTERS := 1024
const MAX_PARTICLES_PER_EMITTER := 100000
const MAX_TOTAL_PARTICLES := 200000

var _document: Dictionary = {}
var _emitters: Array = []
var _states: Dictionary = {}
var _fixed_dt := 1.0 / 60.0
var _max_substeps := 8
var _tick_index := 0
var _simulation_time := 0.0
var _accumulator := 0.0
var _running := true
var _auto_process := false
var _last_error := ""


func configure(document: Dictionary) -> bool:
    var validation_error := _validate_document(document)
    if not validation_error.is_empty():
        _last_error = validation_error
        set_meta("neoeng_particle_error", validation_error)
        return false
    _document = document.duplicate(true)
    _emitters = _ordered_emitters(_document["emitters"])
    _fixed_dt = float(_document["fixed_dt"])
    _max_substeps = int(_document["max_substeps"])
    _states.clear()
    for emitter_value in _emitters:
        var emitter: Dictionary = emitter_value
        _states[str(emitter["id"])] = {
            "rng_state": int(emitter["seed"]),
            "emission_remainder": 0.0,
            "burst_pending": int(emitter["burst_count"]),
            "next_particle_id": 0,
            "particles": [],
        }
    _tick_index = 0
    _simulation_time = 0.0
    _accumulator = 0.0
    _running = true
    _last_error = ""
    set_process(_auto_process)
    _sync_metadata()
    queue_redraw()
    return true


func advance_fixed_ticks(ticks: int) -> bool:
    if ticks < 0 or ticks > 100000 or _document.is_empty():
        return false
    if not _running:
        return false
    for _index in range(ticks):
        _step(_fixed_dt)
        _tick_index += 1
        _simulation_time += _fixed_dt
    _sync_metadata()
    queue_redraw()
    return true


func set_auto_process(value: bool) -> void:
    _auto_process = value
    set_process(value)


func _process(delta: float) -> void:
    if not _auto_process or _document.is_empty() or not _running:
        return
    _accumulator += maxf(delta, 0.0)
    var steps := mini(
        _max_substeps,
        int(floor(_accumulator / _fixed_dt + 0.000000001)),
    )
    for _index in range(steps):
        _step(_fixed_dt)
    if steps > 0:
        _accumulator -= float(steps) * _fixed_dt
        _tick_index += steps
        _simulation_time += float(steps) * _fixed_dt
        _sync_metadata()
        queue_redraw()


func reset_simulation() -> bool:
    if _document.is_empty():
        return false
    return configure(_document)


func set_running(value: bool) -> void:
    _running = value
    _sync_metadata()


func get_particle_count() -> int:
    var count := 0
    for emitter_value in _emitters:
        var emitter: Dictionary = emitter_value
        var state: Dictionary = _states.get(str(emitter["id"]), {})
        count += state.get("particles", []).size()
    return count


func get_emitter_count() -> int:
    return _emitters.size()


func get_state_snapshot() -> Dictionary:
    var particles: Array = []
    var emitters: Array = []
    for emitter_value in _emitters:
        var emitter: Dictionary = emitter_value
        var emitter_id := str(emitter["id"])
        var state: Dictionary = _states[emitter_id]
        emitters.append({
            "id": emitter_id,
            "rng_state": state["rng_state"],
            "emission_remainder": state["emission_remainder"],
            "burst_pending": state["burst_pending"],
            "next_particle_id": state["next_particle_id"],
        })
        for particle_value in state["particles"]:
            var particle: Dictionary = particle_value
            particles.append({
                "id": emitter_id,
                "particle_id": particle["particle_id"],
                "age": particle["age"],
                "position": particle["position"],
                "velocity": particle["velocity"],
            })
    var canonical := {
        "tick_index": _tick_index,
        "simulation_time": _simulation_time,
        "accumulator": _accumulator,
        "emitters": emitters,
        "particles": particles,
    }
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    context.update(JSON.stringify(canonical).to_utf8_buffer())
    return {
        "phase": "running" if _running else "paused",
        "fixed_dt": _fixed_dt,
        "tick_index": _tick_index,
        "simulation_time": _simulation_time,
        "accumulator": _accumulator,
        "particle_count": particles.size(),
        "state_sha256": context.finish().hex_encode(),
    }


func _step(dt: float) -> void:
    for emitter_value in _emitters:
        var emitter: Dictionary = emitter_value
        var emitter_id := str(emitter["id"])
        var state: Dictionary = _states[emitter_id]
        if bool(emitter["enabled"]):
            var particles: Array = state["particles"]
            var available := int(emitter["max_particles"]) - particles.size()
            var burst := mini(int(state["burst_pending"]), maxi(0, available))
            state["burst_pending"] = int(state["burst_pending"]) - burst
            state["emission_remainder"] = float(state["emission_remainder"]) + float(emitter["emission_rate"]) * dt
            var continuous := mini(
                int(floor(float(state["emission_remainder"]))),
                maxi(0, available - burst),
            )
            state["emission_remainder"] = float(state["emission_remainder"]) - continuous
            for _index in range(burst + continuous):
                _spawn(emitter, state)
        var survivors: Array = []
        for particle_value in state["particles"]:
            var particle: Dictionary = particle_value
            var velocity: Array = particle["velocity"]
            var position: Array = particle["position"]
            var acceleration: Dictionary = emitter["acceleration"]
            velocity[0] = float(velocity[0]) + float(acceleration["x"]) * dt
            velocity[1] = float(velocity[1]) + float(acceleration["y"]) * dt
            velocity[2] = float(velocity[2]) + float(acceleration["z"]) * dt
            position[0] = float(position[0]) + float(velocity[0]) * dt
            position[1] = float(position[1]) + float(velocity[1]) * dt
            position[2] = float(position[2]) + float(velocity[2]) * dt
            particle["age"] = float(particle["age"]) + dt
            if float(particle["age"]) < float(emitter["lifetime"]):
                survivors.append(particle)
        state["particles"] = survivors


func _spawn(emitter: Dictionary, state: Dictionary) -> void:
    var random_x = _next_random(state)
    var random_y = _next_random(state)
    var random_z = _next_random(state)
    var velocity: Dictionary = emitter["initial_velocity"]
    var spread: Dictionary = emitter["velocity_spread"]
    var origin: Dictionary = emitter["origin"]
    state["particles"].append({
        "particle_id": int(state["next_particle_id"]),
        "age": 0.0,
        "position": [float(origin["x"]), float(origin["y"]), float(origin["z"])],
        "velocity": [
            float(velocity["x"]) + float(spread["x"]) * (2.0 * random_x - 1.0),
            float(velocity["y"]) + float(spread["y"]) * (2.0 * random_y - 1.0),
            float(velocity["z"]) + float(spread["z"]) * (2.0 * random_z - 1.0),
        ],
    })
    state["next_particle_id"] = int(state["next_particle_id"]) + 1


func _next_random(state: Dictionary) -> float:
    var next_state: int = (1664525 * int(state["rng_state"]) + 1013904223) & UINT32_MASK
    state["rng_state"] = next_state
    return float(next_state) * UINT32_SCALE


func _draw() -> void:
    draw_rect(Rect2(-150.0, -82.0, 300.0, 164.0), Color("101827"), true)
    draw_line(Vector2(-140.0, 0.0), Vector2(140.0, 0.0), Color("40516c"), 1.0)
    draw_line(Vector2(0.0, -72.0), Vector2(0.0, 72.0), Color("40516c"), 1.0)
    var palette := [Color("72d6ff"), Color("ffbb66"), Color("b7f27a"), Color("e5a6ff")]
    var emitter_index := 0
    for emitter_value in _emitters:
        var emitter: Dictionary = emitter_value
        var state: Dictionary = _states.get(str(emitter["id"]), {})
        var color: Color = palette[emitter_index % palette.size()]
        for particle_value in state.get("particles", []):
            var particle: Dictionary = particle_value
            var position: Array = particle["position"]
            var life_ratio := clampf(1.0 - float(particle["age"]) / float(emitter["lifetime"]), 0.0, 1.0)
            draw_circle(Vector2(float(position[0]), float(position[1])), 5.0 + 3.0 * life_ratio, Color(color, life_ratio))
        emitter_index += 1


func _sync_metadata() -> void:
    var snapshot := get_state_snapshot()
    set_meta("neoeng_particle_count", snapshot["particle_count"])
    set_meta("neoeng_particle_emitter_count", _emitters.size())
    set_meta("neoeng_particle_tick", snapshot["tick_index"])
    set_meta("neoeng_particle_state_sha256", snapshot["state_sha256"])
    set_meta("neoeng_particle_phase", snapshot["phase"])


func _ordered_emitters(values: Array) -> Array:
    var remaining := values.duplicate(true)
    var ordered: Array = []
    while not remaining.is_empty():
        var best_index := 0
        for index in range(1, remaining.size()):
            if str(remaining[index]["id"]) < str(remaining[best_index]["id"]):
                best_index = index
        ordered.append(remaining.pop_at(best_index))
    return ordered


func _validate_document(value: Variant) -> String:
    if typeof(value) != TYPE_DICTIONARY:
        return "particle document must be an object"
    var document: Dictionary = value
    if not _exact_keys(document, ["algorithm_version", "emitters", "fixed_dt", "format_id", "max_substeps", "schema_version", "source"]):
        return "particle document keys are invalid"
    if document["format_id"] != "neoeng-d-trace-runtime-particles" or int(document["schema_version"]) != 1 or int(document["algorithm_version"]) != 1:
        return "particle document version is unsupported"
    if typeof(document["source"]) != TYPE_DICTIONARY or not _exact_keys(document["source"], ["format_id", "schema_version", "sha256"]):
        return "particle source binding is invalid"
    var source: Dictionary = document["source"]
    var source_valid: bool = (
        (source["format_id"] == "neoeng-d-trace-scenario-runtime" and int(source["schema_version"]) == 1)
        or (source["format_id"] == "neoeng-d-trace-scene-authoring" and int(source["schema_version"]) == 2)
    )
    if typeof(source["format_id"]) != TYPE_STRING or not _integer_number(source["schema_version"]) or not _lower_hex_hash(source["sha256"]) or not source_valid:
        return "particle source binding is invalid"
    if not _finite_positive(document["fixed_dt"]) or not _integer_number(document["max_substeps"]) or int(document["max_substeps"]) < 1 or int(document["max_substeps"]) > 8:
        return "particle fixed-step configuration is invalid"
    if typeof(document["emitters"]) != TYPE_ARRAY or document["emitters"].is_empty() or document["emitters"].size() > MAX_EMITTERS:
        return "particle emitters are invalid"
    var ids := {}
    var total := 0
    for emitter_value in document["emitters"]:
        if typeof(emitter_value) != TYPE_DICTIONARY:
            return "particle emitter is invalid"
        var emitter: Dictionary = emitter_value
        if not _exact_keys(emitter, ["acceleration", "burst_count", "emission_rate", "enabled", "id", "initial_velocity", "lifetime", "max_particles", "origin", "seed", "velocity_spread"]):
            return "particle emitter keys are invalid"
        var emitter_id := str(emitter["id"])
        if emitter_id.is_empty() or ids.has(emitter_id) or typeof(emitter["id"]) != TYPE_STRING:
            return "particle emitter IDs are invalid"
        ids[emitter_id] = true
        if typeof(emitter["enabled"]) != TYPE_BOOL or not _integer_number(emitter["seed"]) or int(emitter["seed"]) < 0 or int(emitter["seed"]) > UINT32_MASK:
            return "particle emitter seed or enabled flag is invalid"
        if not _finite_non_negative(emitter["emission_rate"]) or not _finite_positive(emitter["lifetime"]):
            return "particle emitter rate or lifetime is invalid"
        if not _integer_number(emitter["max_particles"]) or int(emitter["max_particles"]) < 1 or int(emitter["max_particles"]) > MAX_PARTICLES_PER_EMITTER:
            return "particle emitter capacity is invalid"
        if not _integer_number(emitter["burst_count"]) or int(emitter["burst_count"]) < 0 or int(emitter["burst_count"]) > int(emitter["max_particles"]):
            return "particle emitter burst is invalid"
        total += int(emitter["max_particles"])
        if total > MAX_TOTAL_PARTICLES:
            return "particle document exceeds the capacity limit"
        for vector_name in ["origin", "initial_velocity", "velocity_spread", "acceleration"]:
            if not _valid_vector(emitter[vector_name]):
                return "particle emitter vector is invalid"
    return ""


func _valid_vector(value: Variant) -> bool:
    if typeof(value) != TYPE_DICTIONARY or not _exact_keys(value, ["x", "y", "z"]):
        return false
    return _finite_number(value["x"]) and _finite_number(value["y"]) and _finite_number(value["z"])


func _finite_number(value: Variant) -> bool:
    return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value))


func _integer_number(value: Variant) -> bool:
    return _finite_number(value) and floor(float(value)) == float(value)


func _finite_positive(value: Variant) -> bool:
    return _finite_number(value) and float(value) > 0.0


func _finite_non_negative(value: Variant) -> bool:
    return _finite_number(value) and float(value) >= 0.0


func _lower_hex_hash(value: Variant) -> bool:
    if typeof(value) != TYPE_STRING or String(value).length() != 64:
        return false
    var text := String(value)
    for character in text:
        if not "0123456789abcdef".contains(character):
            return false
    return true


func _exact_keys(value: Variant, expected: Array) -> bool:
    if typeof(value) != TYPE_DICTIONARY:
        return false
    var dictionary: Dictionary = value
    if dictionary.size() != expected.size():
        return false
    for key in expected:
        if not dictionary.has(key):
            return false
    return true
