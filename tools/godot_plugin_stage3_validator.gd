extends SceneTree

const Plugin = preload("res://addons/neoeng_d_trace/plugin.gd")
const ManifestDiagnostic = preload("res://addons/neoeng_d_trace/manifest_diagnostic.gd")


func _fail(message: String) -> void:
    push_error(message)
    quit(1)


func _initialize() -> void:
    var info := Plugin.get_plugin_info()
    if info.get("id") != "neoeng_d_trace":
        _fail("plugin-id")
        return
    if info.get("version") != "0.3.0":
        _fail("plugin-version")
        return
    if not bool(info.get("source_only")) or info.get("binary_dependencies").size() != 0:
        _fail("plugin-source-only")
        return
    var contract := ManifestDiagnostic.get_contract_info()
    if contract.get("format_id") != "neoeng-d-trace-engine-integration":
        _fail("contract-format")
        return
    if contract.get("schema_version") != 1 or contract.get("engine") != "godot":
        _fail("contract-version-engine")
        return
    var result := ManifestDiagnostic.diagnose_manifest("res://NeoEngGenerated/hero.ndt.integration.json")
    if result.get("status") != "SUCCESS":
        _fail("manifest-diagnostic:" + JSON.stringify(result))
        return
    var scan := ManifestDiagnostic.scan_project("res://NeoEngGenerated")
    if scan.get("status") != "SUCCESS" or scan.get("manifests").size() != 1:
        _fail("manifest-scan:" + JSON.stringify(scan))
        return
    print("NATIVE_PLUGIN_STAGE3=SUCCESS")
    print("PLUGIN_ID=" + str(info.get("id")))
    print("PLUGIN_VERSION=" + str(info.get("version")))
    print("DIAGNOSTIC_MANIFESTS=" + str(scan.get("manifests").size()))
    quit(0)