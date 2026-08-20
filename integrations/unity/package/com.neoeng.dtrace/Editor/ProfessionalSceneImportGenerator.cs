using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class ProfessionalSceneImportGenerator
    {
        private const string DefaultExportPath = "Assets/NeoEngGenerated/scene-authoring.unity.json";

        [MenuItem("NeoEng D-Trace/Import Professional Scene")]
        public static void RunFromMenu()
        {
            try
            {
                Selection.activeGameObject = Import(DefaultExportPath);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                throw;
            }
        }

        public static GameObject Import(string exportPath)
        {
            string normalizedPath = NormalizeAssetPath(exportPath);
            string absolutePath = Path.Combine(Directory.GetCurrentDirectory(), normalizedPath);
            if (!File.Exists(absolutePath))
                throw new InvalidDataException("professional scene export does not exist");

            SceneExport export = JsonUtility.FromJson<SceneExport>(File.ReadAllText(absolutePath));
            Validate(export);
            Dictionary<string, AssetData> assets = export.scene.assets.ToDictionary(item => item.id, StringComparer.Ordinal);
            Dictionary<string, GameObject> layers = new Dictionary<string, GameObject>(StringComparer.Ordinal);

            GameObject root = new GameObject("NeoEngProfessionalScene");
            NeoEngProfessionalSceneMetadata sceneMetadata = root.AddComponent<NeoEngProfessionalSceneMetadata>();
            sceneMetadata.sceneHash = export.source.sha256;
            sceneMetadata.sceneName = export.scene.metadata.name;
            sceneMetadata.cameraPosition = new Vector2(export.scene.camera.position.x, export.scene.camera.position.y);
            sceneMetadata.cameraZoom = export.scene.camera.zoom;
            sceneMetadata.serializedGroups = JsonUtility.ToJson(export.scene.groups);
            sceneMetadata.serializedProject = JsonUtility.ToJson(export.scene.project);
            sceneMetadata.serializedSnap = JsonUtility.ToJson(export.scene.snap);

            foreach (LayerData source in export.scene.layers)
            {
                GameObject layer = new GameObject("Layer_" + source.id);
                layer.transform.SetParent(root.transform, false);
                layer.SetActive(source.visible);
                NeoEngProfessionalLayerMetadata metadata = layer.AddComponent<NeoEngProfessionalLayerMetadata>();
                metadata.layerId = source.id;
                metadata.layerName = source.name;
                metadata.visible = source.visible;
                metadata.locked = source.locked;
                ParallaxData parallax = export.scene.parallax_layers.FirstOrDefault(item => item.layer_id == source.id);
                if (parallax != null)
                {
                    metadata.parallaxDepth = parallax.depth;
                    metadata.parallaxTranslationStrength = parallax.translation_strength;
                    metadata.parallaxZoomStrength = parallax.zoom_strength;
                }
                layers.Add(source.id, layer);
            }

            foreach (ObjectData source in export.scene.objects)
            {
                AssetData asset = assets[source.asset_id];
                string assetPath = "Assets/" + asset.path;
                string absoluteAssetPath = Path.Combine(Directory.GetCurrentDirectory(), assetPath.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(absoluteAssetPath) || !string.Equals(FileSha256(absoluteAssetPath), asset.sha256, StringComparison.Ordinal))
                    throw new InvalidDataException("professional scene asset hash does not match: " + asset.path);
                Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(assetPath);
                if (sprite == null)
                    throw new InvalidDataException("professional scene asset is not an imported Sprite: " + asset.path);
                TransformData transform = source.transform;
                GameObject instance = new GameObject("Object_" + source.id);
                instance.transform.SetParent(layers[source.layer_id].transform, false);
                instance.transform.localPosition = new Vector3(
                    transform.position.x,
                    transform.position.y * export.coordinate_mapping.position_y_sign,
                    transform.position.z);
                instance.transform.localEulerAngles = new Vector3(
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z * export.coordinate_mapping.rotation_sign);
                instance.transform.localScale = new Vector3(
                    transform.scale.x * (transform.flip_x ? -1f : 1f),
                    transform.scale.y * (transform.flip_y ? -1f : 1f),
                    transform.scale.z);
                SpriteRenderer renderer = instance.AddComponent<SpriteRenderer>();
                renderer.sprite = sprite;
                renderer.sortingOrder = Mathf.RoundToInt(transform.position.z);
                NeoEngProfessionalObjectMetadata metadata = instance.AddComponent<NeoEngProfessionalObjectMetadata>();
                metadata.objectId = source.id;
                metadata.assetId = source.asset_id;
                metadata.layerId = source.layer_id;
                metadata.locked = source.locked;
                metadata.pivot = new Vector2(transform.pivot.x, transform.pivot.y);
                instance.SetActive(source.visible);
            }

            foreach (SocketData source in export.scene.sockets)
            {
                GameObject marker = new GameObject("Socket_" + source.id);
                marker.transform.SetParent(layers[source.layer_id].transform, false);
                marker.transform.localPosition = new Vector3(
                    source.position.x,
                    source.position.y * export.coordinate_mapping.position_y_sign,
                    source.position.z);
                NeoEngProfessionalSocketMetadata metadata = marker.AddComponent<NeoEngProfessionalSocketMetadata>();
                metadata.socketId = source.id;
                metadata.socketType = source.type;
                metadata.layerId = source.layer_id;
                metadata.objectId = source.object_id;
                metadata.serializedData = JsonUtility.ToJson(source);
            }
            return root;
        }

        public static void RunHeadlessProfessionalSceneImport()
        {
            try
            {
                string path = Environment.GetEnvironmentVariable("NEOENG_PROFESSIONAL_SCENE_EXPORT");
                GameObject root = Import(string.IsNullOrWhiteSpace(path) ? DefaultExportPath : path);
                Debug.Log("UNITY_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS");
                Debug.Log("UNITY_PROFESSIONAL_SCENE_LAYERS=" + root.transform.childCount);
                Debug.Log("UNITY_PROFESSIONAL_SCENE_OBJECTS=" + root.GetComponentsInChildren<NeoEngProfessionalObjectMetadata>().Length);
                UnityEngine.Object.DestroyImmediate(root);
                AssetDatabase.SaveAssets();
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                Debug.LogError("UNITY_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE");
                EditorApplication.Exit(1);
            }
        }

        private static string NormalizeAssetPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) throw new InvalidDataException("professional scene export path is empty");
            string normalized = path.Replace('\\', '/');
            if (normalized.StartsWith("/", StringComparison.Ordinal) || normalized.Contains("..", StringComparison.Ordinal))
                throw new InvalidDataException("professional scene export path is not safe");
            if (!normalized.StartsWith("Assets/", StringComparison.Ordinal))
                throw new InvalidDataException("professional scene export path must be under Assets");
            return normalized;
        }

        private static void Validate(SceneExport export)
        {
            if (export == null || export.format_id != "neoeng-d-trace-scene-authoring-export" || export.schema_version != 1 || export.target != "unity")
                throw new InvalidDataException("professional scene export contract is unsupported");
            if (export.generator == null || export.generator.id != "neoeng_d_trace" || string.IsNullOrWhiteSpace(export.generator.version))
                throw new InvalidDataException("professional scene generator is invalid");
            if (export.source == null || export.scene == null || export.coordinate_mapping == null || export.capabilities == null)
                throw new InvalidDataException("professional scene export is incomplete");
            RequireHash(export.source.sha256, "professional scene source hash");
            if (export.source.format_id != "neoeng-d-trace-scene-authoring" || export.source.schema_version != 2)
                throw new InvalidDataException("professional scene source binding is invalid");
            if (export.coordinate_mapping.position_y_sign != -1 || export.coordinate_mapping.rotation_sign != -1)
                throw new InvalidDataException("Unity professional scene coordinate mapping is invalid");
            if (export.scene.format_id != "neoeng-d-trace-scene-authoring" || export.scene.schema_version != 2 || export.scene.metadata == null || export.scene.project == null || export.scene.snap == null || export.scene.camera == null || export.scene.camera.position == null || export.scene.groups == null || export.scene.parallax_layers == null || export.scene.assets == null || export.scene.layers == null || export.scene.objects == null || export.scene.sockets == null)
                throw new InvalidDataException("professional scene document is invalid");
            HashSet<string> assetIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (AssetData asset in export.scene.assets)
            {
                if (asset == null || string.IsNullOrWhiteSpace(asset.id) || !assetIds.Add(asset.id) || !IsSafeRelative(asset.path) || asset.path_kind != "relative")
                    throw new InvalidDataException("professional scene asset references are invalid");
                RequireHash(asset.sha256, "professional scene asset hash");
            }
            HashSet<string> layerIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (LayerData layer in export.scene.layers)
            {
                if (layer == null || string.IsNullOrWhiteSpace(layer.id) || !layerIds.Add(layer.id))
                    throw new InvalidDataException("professional scene layers are invalid or duplicated");
            }
            HashSet<string> objectIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (ObjectData source in export.scene.objects)
            {
                if (source == null || string.IsNullOrWhiteSpace(source.id) || !objectIds.Add(source.id) || !assetIds.Contains(source.asset_id) || !layerIds.Contains(source.layer_id) || source.transform == null)
                    throw new InvalidDataException("professional scene object references are invalid");
                RequireFiniteTransform(source.transform);
            }
            HashSet<string> socketIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (SocketData socket in export.scene.sockets)
            {
                if (socket == null || string.IsNullOrWhiteSpace(socket.id) || !socketIds.Add(socket.id) || (socket.type != "light" && socket.type != "vfx" && socket.type != "trigger") || !layerIds.Contains(socket.layer_id) || (socket.object_id != null && !objectIds.Contains(socket.object_id)) || socket.position == null)
                    throw new InvalidDataException("professional scene sockets are invalid");
                RequireFinite(socket.position.x, "socket.position.x");
                RequireFinite(socket.position.y, "socket.position.y");
                RequireFinite(socket.position.z, "socket.position.z");
            }
        }

        private static string FileSha256(string path)
        {
            using (SHA256 sha256 = SHA256.Create())
            using (FileStream stream = File.OpenRead(path))
            {
                byte[] digest = sha256.ComputeHash(stream);
                return BitConverter.ToString(digest).Replace("-", "").ToLowerInvariant();
            }
        }

        private static void RequireFiniteTransform(TransformData transform)
        {
            if (transform == null || transform.position == null || transform.rotation == null || transform.scale == null || transform.pivot == null)
                throw new InvalidDataException("professional scene transform is incomplete");
            RequireFinite(transform.position.x, "transform.position.x");
            RequireFinite(transform.position.y, "transform.position.y");
            RequireFinite(transform.position.z, "transform.position.z");
            RequireFinite(transform.rotation.x, "transform.rotation.x");
            RequireFinite(transform.rotation.y, "transform.rotation.y");
            RequireFinite(transform.rotation.z, "transform.rotation.z");
            RequireFinite(transform.scale.x, "transform.scale.x");
            RequireFinite(transform.scale.y, "transform.scale.y");
            RequireFinite(transform.scale.z, "transform.scale.z");
            RequireFinite(transform.pivot.x, "transform.pivot.x");
            RequireFinite(transform.pivot.y, "transform.pivot.y");
            if (transform.pivot.x < 0f || transform.pivot.x > 1f || transform.pivot.y < 0f || transform.pivot.y > 1f || transform.scale.x <= 0f || transform.scale.y <= 0f || transform.scale.z <= 0f)
                throw new InvalidDataException("professional scene scale is invalid");
        }

        private static bool IsSafeRelative(string value)
        {
            return !string.IsNullOrWhiteSpace(value) && !value.Contains("..", StringComparison.Ordinal) && !value.StartsWith("/", StringComparison.Ordinal) && !value.Contains('\\');
        }

        private static void RequireFinite(float value, string field)
        {
            if (float.IsNaN(value) || float.IsInfinity(value)) throw new InvalidDataException(field + " is invalid");
        }

        private static void RequireHash(string value, string field)
        {
            if (string.IsNullOrWhiteSpace(value) || value.Length != 64 || value.Any(character => !"0123456789abcdef".Contains(character)))
                throw new InvalidDataException(field + " is invalid");
        }

        [Serializable] private sealed class SceneExport
        {
            public string format_id;
            public int schema_version;
            public string target;
            public GeneratorData generator;
            public SourceData source;
            public CoordinateMapping coordinate_mapping;
            public CapabilityData capabilities;
            public SceneData scene;
        }
        [Serializable] private sealed class GeneratorData { public string id; public string version; }
        [Serializable] private sealed class SourceData { public string format_id; public int schema_version; public string sha256; }
        [Serializable] private sealed class CoordinateMapping { public string source_origin; public string target_origin; public int position_y_sign; public int rotation_sign; public string rotation_unit; }
        [Serializable] private sealed class CapabilityData { public string[] supported; public string[] unsupported; }
        [Serializable] private sealed class SceneData
        {
            public string format_id;
            public int schema_version;
            public MetadataData metadata;
            public ProjectData project;
            public SnapData snap;
            public AssetData[] assets;
            public LayerData[] layers;
            public ObjectData[] objects;
            public GroupData[] groups;
            public CameraData camera;
            public ParallaxData[] parallax_layers;
            public SocketData[] sockets;
        }
        [Serializable] private sealed class MetadataData { public string name; }
        [Serializable] private sealed class ProjectData { public string sha256; }
        [Serializable] private sealed class SnapData { public bool enabled; public string mode; public PointData spacing; }
        [Serializable] private sealed class AssetData { public string id; public string path; public string path_kind; public string sha256; }
        [Serializable] private sealed class LayerData { public string id; public string name; public bool visible; public bool locked; }
        [Serializable] private sealed class ObjectData { public string id; public string asset_id; public string layer_id; public TransformData transform; public bool visible; public bool locked; }
        [Serializable] private sealed class GroupData { public string id; public string name; public string[] members; public bool visible; public bool locked; }
        [Serializable] private sealed class CameraData { public PointData position; public float zoom; }
        [Serializable] private sealed class TransformData { public Point3Data position; public Point3Data rotation; public Point3Data scale; public PointData pivot; public bool flip_x; public bool flip_y; }
        [Serializable] private sealed class PointData { public float x; public float y; }
        [Serializable] private sealed class Point3Data { public float x; public float y; public float z; }
        [Serializable] private sealed class ParallaxData { public string layer_id; public float depth; public float translation_strength; public float zoom_strength; }
        [Serializable] private sealed class SocketData { public string id; public string layer_id; public string object_id; public Point3Data position; public string type; public string color; public float intensity; public float radius; public string effect_id; public float scale; public bool enabled; public string event_id; public Point3Data size; }
    }
}
