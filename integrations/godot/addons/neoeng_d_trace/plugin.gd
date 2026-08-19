@tool
extends EditorPlugin

const PLUGIN_ID := "neoeng_d_trace"
const PLUGIN_VERSION := "0.3.0"
const MENU_ITEM := "NeoEng D-Trace: Diagnose integration manifests"
const IMPORT_MENU_ITEM := "NeoEng D-Trace: Import integration manifests"
const SCENARIO_MENU_ITEM := "NeoEng D-Trace: Validate scenario runtime export"
const AUTO_SYNC_SETTING := "neoeng_d_trace/automatic_sync_enabled"
const AUTO_SYNC_DEBOUNCE_SECONDS := 0.35
const AUTO_SYNC_SUPPRESSION_MILLISECONDS := 750
const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const ManifestDiagnostic = preload("res://addons/neoeng_d_trace/manifest_diagnostic.gd")
const ScenarioImporter = preload("res://addons/neoeng_d_trace/scenario_importer.gd")

var _sync_timer: Timer
var _sync_running := false
var _suppress_events_until := 0


func _enter_tree() -> void:
    add_tool_menu_item(MENU_ITEM, Callable(self, "_diagnose_project"))
    add_tool_menu_item(IMPORT_MENU_ITEM, Callable(self, "_import_project"))
    add_tool_menu_item(SCENARIO_MENU_ITEM, Callable(self, "_validate_scenario_project"))
    _sync_timer = Timer.new()
    _sync_timer.one_shot = true
    _sync_timer.wait_time = AUTO_SYNC_DEBOUNCE_SECONDS
    add_child(_sync_timer)
    _sync_timer.timeout.connect(_run_automatic_sync)
    var resource_filesystem := get_editor_interface().get_resource_filesystem()
    if resource_filesystem != null:
        resource_filesystem.filesystem_changed.connect(_on_filesystem_changed)


func _exit_tree() -> void:
    var resource_filesystem := get_editor_interface().get_resource_filesystem()
    if resource_filesystem != null and resource_filesystem.filesystem_changed.is_connected(_on_filesystem_changed):
        resource_filesystem.filesystem_changed.disconnect(_on_filesystem_changed)
    if _sync_timer != null:
        _sync_timer.stop()
        _sync_timer.queue_free()
        _sync_timer = null
    remove_tool_menu_item(MENU_ITEM)
    remove_tool_menu_item(IMPORT_MENU_ITEM)
    remove_tool_menu_item(SCENARIO_MENU_ITEM)


func _validate_scenario_project() -> void:
    var result := ScenarioImporter.diagnose_export("res://NeoEngGenerated/scenario.ndtscenario.runtime.json")
    print(JSON.stringify(result, "  "))

func _diagnose_project() -> void:
    var result := ManifestDiagnostic.scan_project("res://NeoEngGenerated")
    print(JSON.stringify(result, "  "))


func _import_project() -> void:
    var result := Importer.import_project("res://NeoEngGenerated")
    print(JSON.stringify(result, "  "))


func _on_filesystem_changed() -> void:
    if not _automatic_sync_enabled() or _sync_running:
        return
    if Time.get_ticks_msec() < _suppress_events_until:
        return
    if _sync_timer != null:
        _sync_timer.start()


func _run_automatic_sync() -> void:
    if not _automatic_sync_enabled() or _sync_running:
        return
    _sync_running = true
    var result: Dictionary = Importer.import_project("res://NeoEngGenerated")
    _sync_running = false
    _suppress_events_until = Time.get_ticks_msec() + AUTO_SYNC_SUPPRESSION_MILLISECONDS
    var status := str(result.get("status", "FAILED"))
    print("NEOENG_GODOT_AUTO_SYNC=" + status)
    print(JSON.stringify({
        "event": "filesystem_changed",
        "status": status,
        "root": "res://NeoEngGenerated",
        "automatic": true,
    }, "  "))


func _automatic_sync_enabled() -> bool:
    return bool(ProjectSettings.get_setting(AUTO_SYNC_SETTING, true))


static func get_plugin_info() -> Dictionary:
    return {
        "id": PLUGIN_ID,
        "name": "NeoEng D-Trace",
        "version": PLUGIN_VERSION,
        "source_only": true,
        "binary_dependencies": [],
        "diagnostic_command": MENU_ITEM,
        "import_command": IMPORT_MENU_ITEM,
    }