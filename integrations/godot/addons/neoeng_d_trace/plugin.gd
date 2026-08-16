@tool
extends EditorPlugin

const PLUGIN_ID := "neoeng_d_trace"
const PLUGIN_VERSION := "0.2.0"
const MENU_ITEM := "NeoEng D-Trace: Diagnose integration manifests"
const IMPORT_MENU_ITEM := "NeoEng D-Trace: Import integration manifests"
const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const ManifestDiagnostic = preload("res://addons/neoeng_d_trace/manifest_diagnostic.gd")


func _enter_tree() -> void:
    add_tool_menu_item(MENU_ITEM, Callable(self, "_diagnose_project"))
    add_tool_menu_item(IMPORT_MENU_ITEM, Callable(self, "_import_project"))


func _exit_tree() -> void:
    remove_tool_menu_item(MENU_ITEM)
    remove_tool_menu_item(IMPORT_MENU_ITEM)


func _diagnose_project() -> void:
    var result := ManifestDiagnostic.scan_project("res://NeoEngGenerated")
    print(JSON.stringify(result, "  "))


func _import_project() -> void:
    var result := Importer.import_project("res://NeoEngGenerated")
    print(JSON.stringify(result, "  "))


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