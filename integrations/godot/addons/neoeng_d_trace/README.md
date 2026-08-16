# NeoEng D-Trace — Godot source-only adapter

This addon is the first native-adapter stage. It is intentionally limited to
identity and read-only diagnostics for the versioned integration manifest.
Sprite2D, pivots, collision polygons, overrides and synchronization are not
implemented by this stage.

## Installation

Copy `addons/neoeng_d_trace` into a Godot project, or copy the contents of a
release ZIP into the project root. The same directory can be consumed from a
Git checkout. Enable `NeoEng D-Trace` in Project Settings > Plugins.

The addon contains only GDScript and configuration. It has no DLL, executable,
native library, automatic download or external runtime dependency.

## Diagnostic command

Use the editor menu `NeoEng D-Trace: Diagnose integration manifests`. It scans
`res://NeoEngGenerated` read-only and reports schema, engine, hash-shape,
relative-path and synchronization-policy errors. It never writes generated
resources.