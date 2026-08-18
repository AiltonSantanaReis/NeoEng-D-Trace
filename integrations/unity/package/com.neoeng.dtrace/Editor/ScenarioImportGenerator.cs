using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class ScenarioImportGenerator
    {
        private const string DefaultExportPath = "Assets/NeoEngGenerated/scenario.ndtscenario.runtime.json";

        public static GameObject ImportScenario(string exportPath)
        {
            string normalizedPath = NormalizeAssetPath(exportPath);
            string absolutePath = Path.Combine(Directory.GetCurrentDirectory(), normalizedPath);
            if (!File.Exists(absolutePath))
            {
                throw new InvalidDataException("scenario runtime export does not exist");
            }
            string text = File.ReadAllText(absolutePath);
            ScenarioExport export = JsonUtility.FromJson<ScenarioExport>(text);
            Validate(export);

            GameObject root = new GameObject("NeoEngScenario");
            NeoEngScenarioMetadata metadata = root.AddComponent<NeoEngScenarioMetadata>();
            metadata.scenarioHash = export.source.sha256;
            metadata.projectHash = export.project.sha256;
            metadata.cameraPosition = new Vector2(export.camera.position.x, export.camera.position.y);
            metadata.cameraZoom = export.camera.zoom;
            for (int index = 0; index < export.layers.Length; index++)
            {
                ScenarioLayerData source = export.layers[index];
                GameObject layerObject = new GameObject("Layer_" + index);
                layerObject.transform.SetParent(root.transform, false);
                layerObject.SetActive(source.visible);
                NeoEngScenarioLayerMetadata layer = layerObject.AddComponent<NeoEngScenarioLayerMetadata>();
                layer.layerId = source.id;
                layer.layerName = source.name;
                layer.visible = source.visible;
                layer.objectIds = source.object_ids ?? Array.Empty<string>();
                layer.parallaxDepth = source.parallax.depth;
                layer.parallaxTranslationStrength = source.parallax.translation_strength;
                layer.parallaxZoomStrength = source.parallax.zoom_strength;
            }
            return root;
        }

        public static void RunHeadlessScenarioImport()
        {
            try
            {
                string path = Environment.GetEnvironmentVariable("NEOENG_SCENARIO_EXPORT");
                GameObject root = ImportScenario(string.IsNullOrWhiteSpace(path) ? DefaultExportPath : path);
                Debug.Log("SCENARIO_ENGINE_STAGE4B4=SUCCESS");
                Debug.Log("SCENARIO_LAYERS=" + root.transform.childCount);
                Debug.Log("SCENARIO_METADATA_ONLY=true");
                UnityEngine.Object.DestroyImmediate(root);
                AssetDatabase.SaveAssets();
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        private static string NormalizeAssetPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) throw new InvalidDataException("scenario export path is empty");
            string normalized = path.Replace('\\', '/');
            if (normalized.StartsWith("/", StringComparison.Ordinal) || normalized.Contains("..", StringComparison.Ordinal))
                throw new InvalidDataException("scenario export path is not safe");
            if (!normalized.StartsWith("Assets/", StringComparison.Ordinal))
                throw new InvalidDataException("scenario export path must be under Assets");
            return normalized;
        }

        private static void Validate(ScenarioExport export)
        {
            if (export == null || export.format_id != "neoeng-d-trace-scenario-runtime" || export.schema_version != 1)
                throw new InvalidDataException("unsupported scenario runtime export");
            if (export.source == null || export.project == null || export.camera == null || export.camera.position == null || export.layers == null)
                throw new InvalidDataException("scenario runtime export is incomplete");
            RequireHash(export.source.sha256, "scenario source hash");
            RequireHash(export.project.sha256, "project hash");
            if (float.IsNaN(export.camera.zoom) || float.IsInfinity(export.camera.zoom) || export.camera.zoom <= 0f)
                throw new InvalidDataException("scenario camera zoom is invalid");
            HashSet<string> layerIds = new HashSet<string>(StringComparer.Ordinal);
            HashSet<string> objectIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (ScenarioLayerData layer in export.layers)
            {
                if (layer == null || string.IsNullOrWhiteSpace(layer.id) || !layerIds.Add(layer.id))
                    throw new InvalidDataException("scenario layer IDs are invalid or duplicated");
                if (layer.object_ids == null || layer.parallax == null)
                    throw new InvalidDataException("scenario layer payload is incomplete");
                foreach (string objectId in layer.object_ids)
                {
                    if (string.IsNullOrWhiteSpace(objectId) || !objectIds.Add(objectId))
                        throw new InvalidDataException("scenario object references are invalid or duplicated");
                }
                RequireUnit(layer.parallax.depth, "scenario parallax depth");
                RequireUnit(layer.parallax.translation_strength, "scenario parallax translation strength");
                RequireUnit(layer.parallax.zoom_strength, "scenario parallax zoom strength");
            }
        }

        private static void RequireHash(string value, string field)
        {
            if (string.IsNullOrWhiteSpace(value) || value.Length != 64 || value.Any(character => !Uri.IsHexDigit(character)))
                throw new InvalidDataException(field + " is invalid");
        }

        private static void RequireUnit(float value, string field)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value < 0f || value > 1f) throw new InvalidDataException(field + " is invalid");
        }

        [Serializable] private sealed class ScenarioExport
        {
            public string format_id;
            public int schema_version;
            public SourceData source;
            public ProjectData project;
            public CameraData camera;
            public ScenarioLayerData[] layers;
        }
        [Serializable] private sealed class SourceData { public string sha256; }
        [Serializable] private sealed class ProjectData { public string sha256; }
        [Serializable] private sealed class CameraData { public PointData position; public float zoom; }
        [Serializable] private sealed class PointData { public float x; public float y; }
        [Serializable] private sealed class ScenarioLayerData
        {
            public string id;
            public string name;
            public bool visible;
            public string[] object_ids;
            public ParallaxData parallax;
        }
        [Serializable] private sealed class ParallaxData
        {
            public float depth;
            public float translation_strength;
            public float zoom_strength;
        }
    }
}
