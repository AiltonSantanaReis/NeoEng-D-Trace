using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class UnityImportGenerator
    {
        private const string GeneratedRoot = "Assets/NeoEngGenerated";
        private const string MarkerFile = ".neoeng-generated";
        private const string PixelsPerUnit = "100";

        [MenuItem("NeoEng D-Trace/Import Integration Manifest")]
        public static void RunFromMenu()
        {
            string manifestPath = FindDefaultManifest();
            ImportResult result = ImportManifest(manifestPath);
            Debug.Log(result.ToJson());
            if (!result.Success)
            {
                throw new InvalidOperationException(result.ErrorSummary());
            }
        }

        public static void RunHeadlessImport()
        {
            string manifestPath = Environment.GetEnvironmentVariable("NEOENG_STAGE6_MANIFEST");
            if (string.IsNullOrWhiteSpace(manifestPath))
            {
                manifestPath = FindDefaultManifest();
            }

            ImportResult result;
            try
            {
                result = ImportManifest(manifestPath);
            }
            catch (Exception exception)
            {
                result = ImportResult.Failure("import_exception", exception.Message);
            }

            string reportPath = Environment.GetEnvironmentVariable("NEOENG_STAGE6_REPORT");
            if (!string.IsNullOrWhiteSpace(reportPath))
            {
                File.WriteAllText(reportPath, result.ToJson() + "\n", new UTF8Encoding(false));
            }

            if (result.Success)
            {
                Debug.Log("UNITY_NATIVE_IMPORT_STAGE6=SUCCESS");
                Debug.Log("IMPORTED_SPRITES=" + result.ImportedSprites);
                Debug.Log("IMPORTED_PREFABS=" + result.ImportedPrefabs);
                Debug.Log("IMPORTED_COLLIDERS=" + result.ImportedColliders);
                return;
            }

            Debug.LogError("UNITY_NATIVE_IMPORT_STAGE6=FAILURE");
            Debug.LogError(result.ErrorSummary());
            EditorApplication.Exit(1);
        }

        public static void CreateManualPrefabFixture()
        {
            Directory.CreateDirectory(ProjectAbsolutePath(GeneratedRoot));
            AssetDatabase.Refresh();
            GameObject manual = new GameObject("ManualFixture");
            PrefabUtility.SaveAsPrefabAsset(manual, GeneratedRoot + "/hero.prefab");
            UnityEngine.Object.DestroyImmediate(manual);

            AssetDatabase.SaveAssets();
        }

        public static ImportResult ImportManifest(string manifestPath)
        {
            string normalizedManifestPath = NormalizeAssetPath(manifestPath);
            string absoluteManifestPath = ProjectAbsolutePath(normalizedManifestPath);
            if (!File.Exists(absoluteManifestPath))
            {
                return ImportResult.Failure("manifest", "integration manifest does not exist");
            }

            IntegrationManifest manifest = JsonUtility.FromJson<IntegrationManifest>(
                File.ReadAllText(absoluteManifestPath, Encoding.UTF8));
            ValidateManifest(manifest);
            string imageAssetPath = ResolveSourceImage(manifest.source.image.path);
            ValidateImageHash(manifest.source.image.sha256, imageAssetPath);
            EnsureGeneratedRootIsControlled();
            AssetDatabase.ImportAsset(imageAssetPath, ImportAssetOptions.ForceUpdate);
            Texture2D texture = AssetDatabase.LoadAssetAtPath<Texture2D>(imageAssetPath);
            if (texture == null)
            {
                return ImportResult.Failure("source_image", "source image could not be loaded by AssetDatabase");
            }

            ImportResult result = ImportResult.SuccessResult(manifest, imageAssetPath);
            foreach (SpriteRecord spriteRecord in manifest.metadata.sprites)
            {
                ImportedAsset asset = ImportSprite(manifest, spriteRecord, texture, imageAssetPath);
                result.Assets.Add(asset);
            }

            result.ImportedSprites = result.Assets.Count;
            result.ImportedPrefabs = result.Assets.Count;
            result.ImportedColliders = result.Assets.Count;

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            ValidateGeneratedAssets(result, manifest);
            return result;
        }

        private static ImportedAsset ImportSprite(
            IntegrationManifest manifest,
            SpriteRecord record,
            Texture2D texture,
            string imageAssetPath)
        {
            string safeId = SafeObjectId(record.id);
            Rect rect = new Rect(record.rect.x, texture.height - record.rect.y - record.rect.h, record.rect.w, record.rect.h);
            if (rect.x < 0 || rect.y < 0 || rect.xMax > texture.width || rect.yMax > texture.height)
            {
                throw new InvalidDataException("sprite rectangle is outside the source image");
            }

            Vector2 pivot = new Vector2(record.pivot_normalized.x, record.pivot_normalized.y);
            Sprite sprite = Sprite.Create(texture, rect, pivot, float.Parse(PixelsPerUnit), 0, SpriteMeshType.FullRect);
            sprite.name = safeId + ".sprite";
            string spritePath = GeneratedRoot + "/" + safeId + ".sprite.asset";
            ReplaceGeneratedAsset(spritePath, sprite);

            Vector2[] polygon = record.polygon_in_sprite ?? Array.Empty<Vector2>();
            if (polygon.Length < 3)
            {
                throw new InvalidDataException("sprite polygon must contain at least three points");
            }

            NeoEngImportedSpriteMetadata metadata = ScriptableObject.CreateInstance<NeoEngImportedSpriteMetadata>();
            metadata.name = safeId + ".metadata";
            metadata.objectId = record.id;
            metadata.generatorId = manifest.generator.id;
            metadata.generatorVersion = manifest.generator.version;
            metadata.sourceImagePath = imageAssetPath;
            metadata.layerId = record.layer;
            metadata.groupId = record.group;
            metadata.trimmed = record.trimmed;
            metadata.padding = record.padding;
            metadata.sourceRect = new Rect(record.rect.x, record.rect.y, record.rect.w, record.rect.h);
            metadata.pivotPixels = new Vector2(record.pivot.x, record.pivot.y);
            metadata.pivotNormalized = pivot;
            metadata.sprite = sprite;
            metadata.polygonInSprite = polygon;
            string metadataPath = GeneratedRoot + "/" + safeId + ".metadata.asset";
            ReplaceGeneratedAsset(metadataPath, metadata);

            GameObject root = new GameObject(safeId);
            SpriteRenderer renderer = root.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            PolygonCollider2D collider = root.AddComponent<PolygonCollider2D>();
            collider.pathCount = 1;
            collider.SetPath(0, ToUnityPoints(polygon, record.rect.h, record.pivot));
            NeoEngGeneratedMarker marker = root.AddComponent<NeoEngGeneratedMarker>();
            marker.generatorId = manifest.generator.id;
            marker.generatorVersion = manifest.generator.version;
            marker.objectId = record.id;
            string prefabPath = GeneratedRoot + "/" + safeId + ".prefab";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) != null)
            {
                AssetDatabase.DeleteAsset(prefabPath);
            }
            GameObject prefab = PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            UnityEngine.Object.DestroyImmediate(root);
            if (prefab == null)
            {
                throw new InvalidOperationException("generated prefab could not be saved");
            }

            return new ImportedAsset
            {
                ObjectId = record.id,
                SpritePath = spritePath,
                MetadataPath = metadataPath,
                PrefabPath = prefabPath,
                ColliderPathCount = 1,
                ColliderPointCount = polygon.Length,
            };
        }

        private static void ValidateGeneratedAssets(ImportResult result, IntegrationManifest manifest)
        {
            foreach (ImportedAsset asset in result.Assets)
            {
                Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(asset.SpritePath);
                NeoEngImportedSpriteMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedSpriteMetadata>(asset.MetadataPath);
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(asset.PrefabPath);
                if (sprite == null || metadata == null || prefab == null)
                {
                    throw new InvalidDataException("generated Unity asset could not be loaded");
                }
                SpriteRenderer renderer = prefab.GetComponent<SpriteRenderer>();
                PolygonCollider2D collider = prefab.GetComponent<PolygonCollider2D>();
                NeoEngGeneratedMarker marker = prefab.GetComponent<NeoEngGeneratedMarker>();
                if (renderer == null || renderer.sprite == null || renderer.sprite.name != sprite.name)
                {
                    throw new InvalidDataException("generated prefab SpriteRenderer is invalid");
                }
                if (collider == null || collider.pathCount != asset.ColliderPathCount || collider.GetPath(0).Length != asset.ColliderPointCount)
                {
                    throw new InvalidDataException("generated PolygonCollider2D is invalid");
                }
                if (marker == null || marker.generatorId != manifest.generator.id || marker.generatorVersion != manifest.generator.version)
                {
                    throw new InvalidDataException("generated prefab marker is invalid");
                }
                if (metadata.sprite == null || metadata.objectId != asset.ObjectId)
                {
                    throw new InvalidDataException("generated ScriptableObject is invalid");
                }
            }
        }

        private static Vector2[] ToUnityPoints(Vector2[] points, float spriteHeight, PivotData pivot)
        {
            return points.Select(point => new Vector2(
                (point.x - pivot.x) / 100f,
                (spriteHeight - point.y - pivot.y) / 100f)).ToArray();
        }

        private static void ReplaceGeneratedAsset(string assetPath, UnityEngine.Object asset)
        {
            if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(assetPath) != null)
            {
                AssetDatabase.DeleteAsset(assetPath);
            }
            AssetDatabase.CreateAsset(asset, assetPath);
        }

        private static void ValidateManifest(IntegrationManifest manifest)
        {
            if (manifest == null || manifest.source == null || manifest.source.image == null || manifest.metadata == null)
            {
                throw new InvalidDataException("integration manifest is incomplete");
            }
            if (manifest.format_id != "neoeng-d-trace-engine-integration" || manifest.schema_version != 1 || manifest.engine != "unity")
            {
                throw new InvalidDataException("integration manifest contract is unsupported");
            }
            if (manifest.generator == null || manifest.generator.id != "neoeng_d_trace" || string.IsNullOrWhiteSpace(manifest.generator.version))
            {
                throw new InvalidDataException("integration generator identity is invalid");
            }
            if (manifest.sync == null || manifest.sync.destructive_update || manifest.sync.generated_root != "NeoEngGenerated")
            {
                throw new InvalidDataException("integration sync policy is invalid");
            }
            if (manifest.metadata.sprites == null || manifest.metadata.sprites.Length == 0)
            {
                throw new InvalidDataException("integration manifest has no sprites");
            }
            if (manifest.source.image.sha256 == null || manifest.source.image.sha256.Length != 64 ||
                manifest.source.metadata == null || manifest.source.metadata.sha256 == null || manifest.source.metadata.sha256.Length != 64)
            {
                throw new InvalidDataException("integration source hashes are invalid");
            }
        }

        private static void ValidateImageHash(string expected, string assetPath)
        {
            string absolutePath = ProjectAbsolutePath(assetPath);
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = File.OpenRead(absolutePath))
            {
                string actual = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
                if (actual != expected)
                {
                    throw new InvalidDataException("source image hash does not match manifest");
                }
            }
        }

        private static string ResolveSourceImage(string reference)
        {
            string normalized = NormalizeRelativeReference(reference);
            string assetPath = normalized.StartsWith("Assets/", StringComparison.Ordinal)
                ? normalized
                : "Assets/" + normalized;
            string absolute = ProjectAbsolutePath(assetPath);
            if (!File.Exists(absolute))
            {
                throw new FileNotFoundException("source image does not exist");
            }
            return assetPath;
        }

        private static string FindDefaultManifest()
        {
            string[] paths = AssetDatabase.FindAssets("t:TextAsset", new[] { "Assets" })
                .Select(AssetDatabase.GUIDToAssetPath)
                .Where(path => path.EndsWith(".ndt.integration.json", StringComparison.OrdinalIgnoreCase))
                .OrderBy(path => path, StringComparer.Ordinal)
                .ToArray();
            if (paths.Length == 0)
            {
                throw new FileNotFoundException("no integration manifest was found under Assets");
            }
            return paths[0];
        }

        private static void EnsureGeneratedRootIsControlled()
        {
            string absoluteRoot = ProjectAbsolutePath(GeneratedRoot);
            Directory.CreateDirectory(absoluteRoot);
            string marker = Path.Combine(absoluteRoot, MarkerFile);
            if (!File.Exists(marker) && Directory.GetFiles(absoluteRoot, "*", SearchOption.AllDirectories).Length > 0)
            {
                throw new InvalidOperationException("generated root contains manual content and is not controlled");
            }
            if (!File.Exists(marker))
            {
                File.WriteAllText(marker, "generator=neoeng_d_trace\nversion=0.2.0\n", new UTF8Encoding(false));
                AssetDatabase.Refresh();
            }
        }

        private static string SafeObjectId(string value)
        {
            if (string.IsNullOrWhiteSpace(value) || value.Any(character => !(char.IsLetterOrDigit(character) || character == '_' || character == '-')))
            {
                throw new InvalidDataException("sprite id is not safe for generated asset names");
            }
            return value;
        }

        private static string NormalizeAssetPath(string path)
        {
            string normalized = NormalizeRelativeReference(path);
            if (!normalized.StartsWith("Assets/", StringComparison.Ordinal))
            {
                throw new InvalidDataException("manifest path must be under Assets");
            }
            return normalized;
        }

        private static string NormalizeRelativeReference(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || path.Contains("\\") || path.StartsWith("/", StringComparison.Ordinal) || path.Contains(":") || path.Split('/').Contains(".."))
            {
                throw new InvalidDataException("path must be relative and safe");
            }
            return path.TrimStart('.', '/');
        }

        private static string ProjectAbsolutePath(string assetPath)
        {
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string relative = assetPath.StartsWith("Assets/", StringComparison.Ordinal)
                ? assetPath.Substring("Assets/".Length)
                : assetPath;
            return Path.Combine(Application.dataPath, relative.Replace('/', Path.DirectorySeparatorChar));
        }

        [Serializable]
        public sealed class IntegrationManifest
        {
            public string format_id;
            public int schema_version;
            public GeneratorData generator;
            public string engine;
            public SourceData source;
            public SyncData sync;
            public MetadataData metadata;
        }

        [Serializable] public sealed class GeneratorData { public string id; public string version; }
        [Serializable] public sealed class SourceData { public ImageData image; public MetadataHashData metadata; }
        [Serializable] public sealed class ImageData { public string path; public string sha256; }
        [Serializable] public sealed class MetadataHashData { public string format_id; public int schema_version; public string sha256; }
        [Serializable] public sealed class SyncData { public string direction; public string generated_root; public string override_suffix; public bool destructive_update; }
        [Serializable] public sealed class MetadataData { public int schema_version; public SpriteRecord[] sprites; }
        [Serializable] public sealed class SpriteRecord
        {
            public string id;
            public string layer;
            public string group;
            public bool trimmed;
            public int padding;
            public RectData rect;
            public PivotData pivot;
            public PivotData pivot_normalized;
            public Vector2[] polygon_in_sprite;
            public CollisionData collision;
        }
        [Serializable] public sealed class RectData { public float x; public float y; public float w; public float h; }
        [Serializable] public sealed class PivotData { public float x; public float y; }
        [Serializable] public sealed class CollisionData { public string shape_type; public Vector2[] points; }

        [Serializable]
        public sealed class ImportResult
        {
            public bool Success;
            public string ErrorCode;
            public string Error;
            public string SourceImagePath;
            public int ImportedSprites;
            public int ImportedPrefabs;
            public int ImportedColliders;
            public List<ImportedAsset> Assets = new List<ImportedAsset>();

            public static ImportResult SuccessResult(IntegrationManifest manifest, string sourceImagePath)
            {
                return new ImportResult { Success = true, SourceImagePath = sourceImagePath };
            }

            public static ImportResult Failure(string code, string error)
            {
                return new ImportResult { Success = false, ErrorCode = code, Error = error };
            }

            public string ErrorSummary() { return ErrorCode + ": " + Error; }
            public string ToJson() { return JsonUtility.ToJson(this, true); }
        }

        [Serializable]
        public sealed class ImportedAsset
        {
            public string ObjectId;
            public string SpritePath;
            public string MetadataPath;
            public string PrefabPath;
            public int ColliderPathCount;
            public int ColliderPointCount;
        }
    }
}
