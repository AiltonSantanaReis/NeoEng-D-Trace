using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class UnityImportGenerator
    {
        private const string GeneratedRoot = "Assets/NeoEngGenerated";
        private const string MarkerFile = ".neoeng-generated";
        private const float LegacyPixelsPerUnit = 100f;
        private const string ConfirmDestructiveEnvironment = "NEOENG_STAGE7_CONFIRM_DESTRUCTIVE";

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
            catch (SyncConflictException exception)
            {
                result = ImportResult.Failure("sync_conflict", exception.Message);
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
                Debug.Log("UNITY_NATIVE_SYNC_STAGE7=SUCCESS");
                if (Environment.GetEnvironmentVariable("NEOENG_STAGE8_MODE") == "advanced")
                {
                    Debug.Log("UNITY_NATIVE_IMPORT_STAGE8=SUCCESS");
                }
                Debug.Log("IMPORTED_SPRITES=" + result.ImportedSprites);
                Debug.Log("IMPORTED_PREFABS=" + result.ImportedPrefabs);
                Debug.Log("IMPORTED_COLLIDERS=" + result.ImportedColliders);
                return;
            }

            Debug.LogError("UNITY_NATIVE_IMPORT_STAGE6=FAILURE");
            Debug.LogError("UNITY_NATIVE_SYNC_STAGE7=FAILURE");
            Debug.LogError(result.ErrorSummary());
            EditorApplication.Exit(1);
        }

        public static void RunHeadlessAdvancedImport()
        {
            Environment.SetEnvironmentVariable("NEOENG_STAGE8_MODE", "advanced");
            RunHeadlessImport();
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

        public static void MutateGeneratedPrefabFixture()
        {
            const string prefabPath = GeneratedRoot + "/hero.prefab";
            GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
            if (root == null)
            {
                throw new InvalidOperationException("generated prefab fixture does not exist");
            }
            PolygonCollider2D collider = root.GetComponent<PolygonCollider2D>();
            if (collider == null || collider.pathCount != 1)
            {
                PrefabUtility.UnloadPrefabContents(root);
                throw new InvalidOperationException("generated prefab collider fixture is invalid");
            }
            Vector2[] points = collider.GetPath(0);
            points[0] += new Vector2(0.25f, 0.0f);
            collider.SetPath(0, points);
            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            PrefabUtility.UnloadPrefabContents(root);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            Debug.Log("UNITY_NATIVE_SYNC_STAGE7_MUTATION=APPLIED");
        }
        public static ImportResult ImportManifest(string manifestPath)
        {
            string normalizedManifestPath = NormalizeAssetPath(manifestPath);
            string absoluteManifestPath = ProjectAbsolutePath(normalizedManifestPath);
            if (!File.Exists(absoluteManifestPath))
            {
                return ImportResult.Failure("manifest", "integration manifest does not exist");
            }

            string manifestText = File.ReadAllText(absoluteManifestPath, Encoding.UTF8);
            IntegrationManifest manifest = JsonUtility.FromJson<IntegrationManifest>(manifestText);
            ApplyPolygonArrays(manifest, manifestText);
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
            Dictionary<string, Texture2D> atlasTextures = LoadAdvancedAtlasTextures(manifest, imageAssetPath, texture);

            ImportResult result = ImportResult.SuccessResult(manifest, imageAssetPath);
            foreach (SpriteRecord spriteRecord in manifest.metadata.sprites)
            {
                ImportedAsset asset = ImportSprite(manifest, spriteRecord, texture, imageAssetPath, atlasTextures);
                result.Assets.Add(asset);
                if (asset.Status == "UNCHANGED")
                {
                    result.UnchangedAssets++;
                }
                else
                {
                    result.UpdatedAssets++;
                }
                if (asset.OverrideApplied)
                {
                    result.OverridesApplied++;
                }
            }

            result.ImportedSprites = result.Assets.Count;
            result.ImportedPrefabs = result.Assets.Count;
            result.ImportedColliders = result.Assets.Count;

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            ValidateGeneratedAssets(result, manifest);
            return result;
        }

        private static Dictionary<string, Texture2D> LoadAdvancedAtlasTextures(
            IntegrationManifest manifest,
            string sourceImageAssetPath,
            Texture2D sourceTexture)
        {
            Dictionary<string, Texture2D> textures = new Dictionary<string, Texture2D>();
            textures["__source__"] = sourceTexture;
            if (manifest.schema_version != 2)
            {
                return textures;
            }
            ValidateAdvancedManifest(manifest);
            foreach (AtlasPageData page in manifest.advanced.atlas.pages)
            {
                string assetPath = ResolveSourceImage(page.path);
                ValidateImageHash(page.sha256, assetPath);
                AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
                Texture2D atlasTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
                if (atlasTexture == null)
                {
                    throw new InvalidDataException("advanced atlas page could not be loaded");
                }
                ApplyTextureProperties(assetPath, manifest.advanced.engine_properties.unity);
                atlasTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
                if (atlasTexture == null || atlasTexture.width != page.width || atlasTexture.height != page.height)
                {
                    throw new InvalidDataException("advanced atlas page dimensions mismatch: expected " + page.width + "x" + page.height + ", actual " + (atlasTexture == null ? "null" : atlasTexture.width + "x" + atlasTexture.height));
                }
                textures[page.id] = atlasTexture;
            }
            return textures;
        }

        private static void ApplyTextureProperties(string assetPath, UnityProperties properties)
        {
            TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (importer == null)
            {
                throw new InvalidDataException("advanced atlas page is not a texture importer asset");
            }
            importer.textureType = TextureImporterType.Sprite;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.filterMode = properties.filter_mode == "Point" ? FilterMode.Point : FilterMode.Bilinear;
            importer.wrapMode = properties.wrap_mode == "Clamp" ? TextureWrapMode.Clamp :
                properties.wrap_mode == "Repeat" ? TextureWrapMode.Repeat : TextureWrapMode.Mirror;
            importer.SaveAndReimport();
        }

        private static AtlasSpriteData FindAdvancedSprite(IntegrationManifest manifest, string objectId, out AtlasPageData page)
        {
            page = null;
            if (manifest.schema_version != 2)
            {
                return null;
            }
            foreach (AtlasPageData candidate in manifest.advanced.atlas.pages)
            {
                foreach (AtlasSpriteData sprite in candidate.sprites)
                {
                    if (sprite.id == objectId)
                    {
                        page = candidate;
                        return sprite;
                    }
                }
            }
            throw new InvalidDataException("advanced atlas sprite is missing: " + objectId);
        }

        private static float PixelsPerUnit(IntegrationManifest manifest)
        {
            return manifest.schema_version == 2
                ? manifest.advanced.engine_properties.unity.pixels_per_unit
                : LegacyPixelsPerUnit;
        }

        private static Vector2 EffectivePivot(PivotData pivot, RectData logicalRect, AtlasSpriteData atlasSprite)
        {
            Vector2 normalized = new Vector2(pivot.x / logicalRect.w, pivot.y / logicalRect.h);
            if (atlasSprite != null && atlasSprite.rotated)
            {
                return new Vector2(1f - normalized.y, normalized.x);
            }
            return normalized;
        }

        private static Vector2[] EffectivePolygon(Vector2[] polygon, RectData logicalRect, AtlasSpriteData atlasSprite)
        {
            if (atlasSprite == null || !atlasSprite.rotated)
            {
                return polygon;
            }
            return polygon.Select(point => new Vector2(logicalRect.h - point.y, point.x)).ToArray();
        }
        private static ImportedAsset ImportSprite(
            IntegrationManifest manifest,
            SpriteRecord record,
            Texture2D texture,
            string imageAssetPath,
            Dictionary<string, Texture2D> atlasTextures)
        {
            string safeId = SafeObjectId(record.id);
            AtlasPageData atlasPage;
            AtlasSpriteData atlasSprite = FindAdvancedSprite(manifest, record.id, out atlasPage);
            Texture2D effectiveTexture = texture;
            RectData logicalRect = record.rect;
            RectData regionData = atlasSprite == null ? record.rect : atlasSprite.rect;
            if (atlasSprite != null)
            {
                if (!atlasTextures.ContainsKey(atlasPage.id))
                {
                    throw new InvalidDataException("advanced atlas texture is not loaded");
                }
                effectiveTexture = atlasTextures[atlasPage.id];
            }
            Rect rect = new Rect(regionData.x, effectiveTexture.height - regionData.y - regionData.h, regionData.w, regionData.h);
            if (rect.x < 0 || rect.y < 0 || rect.xMax > effectiveTexture.width || rect.yMax > effectiveTexture.height)
            {
                throw new InvalidDataException("sprite rectangle is outside the source image");
            }

            Vector2 pivot = EffectivePivot(record.pivot, logicalRect, atlasSprite);
            float pixelsPerUnit = PixelsPerUnit(manifest);
            int extrusion = atlasSprite == null ? 0 : atlasSprite.extrusion;
            Sprite sprite = Sprite.Create(effectiveTexture, rect, pivot, pixelsPerUnit, (uint)extrusion, SpriteMeshType.FullRect);
            sprite.name = safeId + ".sprite";
            string spritePath = GeneratedRoot + "/" + safeId + ".sprite.asset";

            Vector2[] polygon = record.polygon_in_sprite ?? Array.Empty<Vector2>();
            if (polygon.Length < 3)
            {
                throw new InvalidDataException("sprite polygon must contain at least three points");
            }
            OverrideData overrideData = ReadOverride(safeId, record.id);
            Vector2[] effectivePolygon = EffectivePolygon(overrideData.Polygon ?? polygon, logicalRect, atlasSprite);
            Vector2 effectivePivotPixels = new Vector2(pivot.x * regionData.w, pivot.y * regionData.h);
            string expectedFingerprint = ComputeFingerprint(record.id, safeId + ".sprite", ToUnityPoints(effectivePolygon, regionData.h, effectivePivotPixels, pixelsPerUnit));
            string prefabPath = GeneratedRoot + "/" + safeId + ".prefab";
            ExistingSync existing = InspectExistingPrefab(prefabPath, manifest, expectedFingerprint, overrideData.Hash);
            if (existing.Unchanged)
            {
                return new ImportedAsset
                {
                    ObjectId = record.id,
                    SpritePath = spritePath,
                    MetadataPath = GeneratedRoot + "/" + safeId + ".metadata.asset",
                    PrefabPath = prefabPath,
                    ColliderPathCount = 1,
                    ColliderPointCount = effectivePolygon.Length,
                    Status = "UNCHANGED",
                    OverrideApplied = overrideData.Polygon != null,
                };
            }
            ReplaceGeneratedAsset(spritePath, sprite);
            NeoEngImportedSpriteMetadata metadata = ScriptableObject.CreateInstance<NeoEngImportedSpriteMetadata>();
            metadata.name = safeId + ".metadata";
            metadata.objectId = record.id;
            metadata.generatorId = manifest.generator.id;
            metadata.generatorVersion = manifest.generator.version;
            metadata.sourceImagePath = imageAssetPath;
            metadata.sourceImageHash = manifest.source.image.sha256;
            metadata.sourceMetadataHash = manifest.source.metadata.sha256;
            metadata.overrideHash = overrideData.Hash;
            metadata.generatedFingerprint = expectedFingerprint;
            metadata.layerId = record.layer;
            metadata.groupId = record.group;
            metadata.trimmed = record.trimmed;
            metadata.padding = record.padding;
            metadata.sourceRect = new Rect(regionData.x, regionData.y, regionData.w, regionData.h);
            metadata.pivotPixels = effectivePivotPixels;
            metadata.pivotNormalized = pivot;
            metadata.sprite = sprite;
            metadata.polygonInSprite = effectivePolygon;
            string metadataPath = GeneratedRoot + "/" + safeId + ".metadata.asset";
            ReplaceGeneratedAsset(metadataPath, metadata);

            GameObject root = new GameObject(safeId);
            SpriteRenderer renderer = root.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            if (manifest.schema_version == 2)
            {
                renderer.sortingLayerName = manifest.advanced.engine_properties.unity.sorting_layer;
                renderer.sortingOrder = manifest.advanced.engine_properties.unity.sorting_order;
                root.transform.position = new Vector3(0f, 0f, manifest.advanced.engine_properties.unity.z_depth);
            }
            PolygonCollider2D collider = root.AddComponent<PolygonCollider2D>();
            collider.pathCount = 1;
            collider.SetPath(0, ToUnityPoints(effectivePolygon, regionData.h, effectivePivotPixels, pixelsPerUnit));
            NeoEngGeneratedMarker marker = root.AddComponent<NeoEngGeneratedMarker>();
            marker.generatorId = manifest.generator.id;
            marker.generatorVersion = manifest.generator.version;
            marker.objectId = record.id;
            marker.sourceImageHash = manifest.source.image.sha256;
            marker.sourceMetadataHash = manifest.source.metadata.sha256;
            marker.overrideHash = overrideData.Hash;
            marker.generatedFingerprint = expectedFingerprint;
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
                ColliderPointCount = effectivePolygon.Length,
                Status = "UPDATED",
                OverrideApplied = overrideData.Polygon != null,
            };
        }

        private static ExistingSync InspectExistingPrefab(
            string prefabPath,
            IntegrationManifest manifest,
            string expectedFingerprint,
            string overrideHash)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                return ExistingSync.NewAsset();
            }
            NeoEngGeneratedMarker marker = prefab.GetComponent<NeoEngGeneratedMarker>();
            SpriteRenderer renderer = prefab.GetComponent<SpriteRenderer>();
            PolygonCollider2D collider = prefab.GetComponent<PolygonCollider2D>();
            if (marker == null || renderer == null || renderer.sprite == null || collider == null ||
                string.IsNullOrWhiteSpace(marker.sourceImageHash) ||
                string.IsNullOrWhiteSpace(marker.sourceMetadataHash) ||
                string.IsNullOrWhiteSpace(marker.generatedFingerprint))
            {
                return RequireDestructiveConfirmation("generated Unity output has no synchronization state or contains manual content", prefabPath);
            }
            string actualFingerprint = ComputePrefabFingerprint(prefab);
            if (actualFingerprint != marker.generatedFingerprint)
            {
                return RequireDestructiveConfirmation("generated Unity output was manually modified", prefabPath);
            }
            bool sameSource = marker.sourceImageHash == manifest.source.image.sha256 &&
                marker.sourceMetadataHash == manifest.source.metadata.sha256 &&
                marker.overrideHash == overrideHash;
            if (sameSource && marker.generatedFingerprint == expectedFingerprint)
            {
                return ExistingSync.UnchangedAsset();
            }
            return ExistingSync.UpdateAsset();
        }

        private static ExistingSync RequireDestructiveConfirmation(string message, string path)
        {
            if (!IsDestructiveUpdateConfirmed())
            {
                throw new SyncConflictException(message + ": " + path);
            }
            return ExistingSync.UpdateAsset();
        }

        private static bool IsDestructiveUpdateConfirmed()
        {
            string value = Environment.GetEnvironmentVariable(ConfirmDestructiveEnvironment);
            return string.Equals(value, "1", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(value, "true", StringComparison.OrdinalIgnoreCase);
        }

        private static OverrideData ReadOverride(string safeId, string objectId)
        {
            string assetPath = GeneratedRoot + "/" + safeId + PackageIdentity.OverrideSuffix;
            string absolutePath = ProjectAbsolutePath(assetPath);
            if (!File.Exists(absolutePath))
            {
                return OverrideData.None();
            }
            string content = File.ReadAllText(absolutePath, Encoding.UTF8);
            OverridePayload payload = JsonUtility.FromJson<OverridePayload>(content);
            if (payload == null || payload.object_id != objectId || payload.polygon_in_sprite == null || payload.polygon_in_sprite.Length < 3)
            {
                throw new InvalidDataException("Unity override is invalid for generated object");
            }
            foreach (Vector2 point in payload.polygon_in_sprite)
            {
                if (float.IsNaN(point.x) || float.IsNaN(point.y) || float.IsInfinity(point.x) || float.IsInfinity(point.y))
                {
                    throw new InvalidDataException("Unity override contains non-finite polygon coordinates");
                }
            }
            return new OverrideData
            {
                Polygon = payload.polygon_in_sprite,
                Hash = ComputeSha256(Encoding.UTF8.GetBytes(content)),
            };
        }

        private static string ComputePrefabFingerprint(GameObject prefab)
        {
            SpriteRenderer renderer = prefab.GetComponent<SpriteRenderer>();
            PolygonCollider2D collider = prefab.GetComponent<PolygonCollider2D>();
            NeoEngGeneratedMarker marker = prefab.GetComponent<NeoEngGeneratedMarker>();
            Vector2[] points = collider.GetPath(0);
            string signature = marker.objectId + "|" + renderer.sprite.name + "|" +
                string.Join(";", points.Select(FormatPoint));
            return ComputeSha256(Encoding.UTF8.GetBytes(signature));
        }

        private static string ComputeFingerprint(string objectId, string spriteName, Vector2[] points)
        {
            string signature = objectId + "|" + spriteName + "|" +
                string.Join(";", points.Select(FormatPoint));
            return ComputeSha256(Encoding.UTF8.GetBytes(signature));
        }

        private static string FormatPoint(Vector2 point)
        {
            return Math.Round(point.x, 6).ToString("0.######", System.Globalization.CultureInfo.InvariantCulture) + "," + Math.Round(point.y, 6).ToString("0.######", System.Globalization.CultureInfo.InvariantCulture);
        }

        private static string ComputeSha256(byte[] bytes)
        {
            using (SHA256 sha = SHA256.Create())
            {
                return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
            }
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
                if (manifest.schema_version == 2)
                {
                    AtlasPageData atlasPage;
                    AtlasSpriteData atlasSprite = FindAdvancedSprite(manifest, asset.ObjectId, out atlasPage);
                    UnityProperties properties = manifest.advanced.engine_properties.unity;
                    if (Math.Abs(sprite.pixelsPerUnit - properties.pixels_per_unit) > 0.0001f || renderer.sortingLayerName != properties.sorting_layer || renderer.sortingOrder != properties.sorting_order || Math.Abs(prefab.transform.position.z - properties.z_depth) > 0.0001f || atlasSprite == null || atlasSprite.extrusion != manifest.advanced.atlas.bleed)
                    {
                        throw new InvalidDataException("generated advanced Unity properties are invalid");
                    }
                }
            }
        }

        private static Vector2[] ToUnityPoints(Vector2[] points, float spriteHeight, Vector2 pivotPixels, float pixelsPerUnit)
        {
            return points.Select(point => new Vector2(
                (point.x - pivotPixels.x) / pixelsPerUnit,
                (spriteHeight - point.y - pivotPixels.y) / pixelsPerUnit)).ToArray();
        }

        private static void ReplaceGeneratedAsset(string assetPath, UnityEngine.Object asset)
        {
            if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(assetPath) != null)
            {
                AssetDatabase.DeleteAsset(assetPath);
            }
            AssetDatabase.CreateAsset(asset, assetPath);
        }

        private static void ApplyPolygonArrays(IntegrationManifest manifest, string manifestText)
        {
            if (manifest == null || manifest.metadata == null || manifest.metadata.sprites == null)
            {
                return;
            }

            MatchCollection matches = Regex.Matches(
                manifestText,
                "\"polygon_in_sprite\"\\s*:\\s*\\[",
                RegexOptions.CultureInvariant);
            if (matches.Count != manifest.metadata.sprites.Length)
            {
                throw new InvalidDataException("manifest polygon count does not match sprite count");
            }

            for (int index = 0; index < matches.Count; index++)
            {
                int opening = manifestText.IndexOf('[', matches[index].Index);
                string arrayText = ExtractBalancedArray(manifestText, opening);
                MatchCollection points = Regex.Matches(
                    arrayText,
                    @"\[\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*\]",
                    RegexOptions.CultureInvariant);
                if (points.Count < 3)
                {
                    throw new InvalidDataException("manifest sprite polygon must contain at least three points");
                }

                Vector2[] polygon = new Vector2[points.Count];
                for (int pointIndex = 0; pointIndex < points.Count; pointIndex++)
                {
                    float x = float.Parse(points[pointIndex].Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
                    float y = float.Parse(points[pointIndex].Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture);
                    polygon[pointIndex] = new Vector2(x, y);
                }
                manifest.metadata.sprites[index].polygon_in_sprite = polygon;
            }
        }

        private static string ExtractBalancedArray(string text, int opening)
        {
            if (opening < 0 || opening >= text.Length || text[opening] != '[')
            {
                throw new InvalidDataException("manifest polygon array is invalid");
            }

            int depth = 0;
            for (int index = opening; index < text.Length; index++)
            {
                if (text[index] == '[')
                {
                    depth++;
                }
                else if (text[index] == ']')
                {
                    depth--;
                    if (depth == 0)
                    {
                        return text.Substring(opening, index - opening + 1);
                    }
                }
            }
            throw new InvalidDataException("manifest polygon array is unterminated");
        }
        private static void ValidateManifest(IntegrationManifest manifest)
        {
            if (manifest == null || manifest.source == null || manifest.source.image == null || manifest.metadata == null)
            {
                throw new InvalidDataException("integration manifest is incomplete");
            }
            if (manifest.format_id != "neoeng-d-trace-engine-integration" || (manifest.schema_version != 1 && manifest.schema_version != 2) || manifest.engine != "unity")
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
            if (manifest.schema_version == 2)
            {
                ValidateAdvancedManifest(manifest);
            }
        }

        private static void ValidateAdvancedManifest(IntegrationManifest manifest)
        {
            AdvancedData advanced = manifest.advanced;
            if (advanced == null || advanced.schema_version != 1 || advanced.coordinate_system == null || advanced.atlas == null || advanced.engine_properties == null)
            {
                throw new InvalidDataException("advanced integration contract is incomplete");
            }
            if (advanced.coordinate_system.image_origin != "top-left" || advanced.coordinate_system.polygon_origin != "sprite-top-left" || advanced.coordinate_system.engine_y_axis != "up" || advanced.coordinate_system.pixels_per_unit == null)
            {
                throw new InvalidDataException("advanced coordinate contract is invalid");
            }
            if (advanced.coordinate_system.pixels_per_unit.godot <= 0f || advanced.coordinate_system.pixels_per_unit.unity <= 0f)
            {
                throw new InvalidDataException("advanced pixels-per-unit values are invalid");
            }
            if (advanced.atlas.pages == null || advanced.atlas.pages.Length == 0 || advanced.atlas.bleed < 0)
            {
                throw new InvalidDataException("advanced atlas contract is invalid");
            }
            HashSet<string> ids = new HashSet<string>(StringComparer.Ordinal);
            foreach (AtlasPageData page in advanced.atlas.pages)
            {
                if (page == null || string.IsNullOrWhiteSpace(page.id) || string.IsNullOrWhiteSpace(page.path) || page.sha256 == null || page.sha256.Length != 64 || page.width <= 0 || page.height <= 0 || page.sprites == null || page.sprites.Length == 0)
                {
                    throw new InvalidDataException("advanced atlas page contract is invalid");
                }
                foreach (AtlasSpriteData sprite in page.sprites)
                {
                    if (sprite == null || string.IsNullOrWhiteSpace(sprite.id) || !ids.Add(sprite.id) || sprite.rect == null || sprite.packed_rect == null || sprite.rect.w <= 0f || sprite.rect.h <= 0f || sprite.packed_rect.w <= 0f || sprite.packed_rect.h <= 0f || sprite.extrusion != advanced.atlas.bleed)
                    {
                        throw new InvalidDataException("advanced atlas sprite contract is invalid");
                    }
                }
            }
            UnityProperties unity = advanced.engine_properties.unity;
            GodotProperties godot = advanced.engine_properties.godot;
            if (unity == null || unity.pixels_per_unit <= 0f || (unity.filter_mode != "Point" && unity.filter_mode != "Bilinear") || (unity.wrap_mode != "Clamp" && unity.wrap_mode != "Repeat" && unity.wrap_mode != "Mirror") || string.IsNullOrWhiteSpace(unity.sorting_layer) || float.IsNaN(unity.z_depth) || float.IsInfinity(unity.z_depth))
            {
                throw new InvalidDataException("advanced Unity properties are invalid");
            }
            if (godot == null || (godot.texture_filter != "nearest" && godot.texture_filter != "linear") || (godot.texture_repeat != "disabled" && godot.texture_repeat != "enabled"))
            {
                throw new InvalidDataException("advanced Godot properties are invalid");
            }
            HashSet<string> metadataIds = new HashSet<string>(manifest.metadata.sprites.Select(item => item.id), StringComparer.Ordinal);
            if (!ids.SetEquals(metadataIds))
            {
                throw new InvalidDataException("advanced atlas sprites do not match metadata sprites");
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
            public AdvancedData advanced;
        }

        [Serializable] public sealed class GeneratorData { public string id; public string version; }
        [Serializable] public sealed class SourceData { public ImageData image; public MetadataHashData metadata; }
        [Serializable] public sealed class ImageData { public string path; public string sha256; }
        [Serializable] public sealed class MetadataHashData { public string format_id; public int schema_version; public string sha256; }
        [Serializable] public sealed class SyncData { public string direction; public string generated_root; public string override_suffix; public bool destructive_update; }
        [Serializable] public sealed class MetadataData { public int schema_version; public SpriteRecord[] sprites; }
        [Serializable] public sealed class AdvancedData { public int schema_version; public CoordinateSystemData coordinate_system; public AtlasData atlas; public EnginePropertiesData engine_properties; }
        [Serializable] public sealed class CoordinateSystemData { public string image_origin; public string polygon_origin; public string engine_y_axis; public PixelsPerUnitData pixels_per_unit; }
        [Serializable] public sealed class PixelsPerUnitData { public float godot; public float unity; }
        [Serializable] public sealed class AtlasData { public int bleed; public AtlasPageData[] pages; }
        [Serializable] public sealed class AtlasPageData { public string id; public string path; public string sha256; public int width; public int height; public AtlasSpriteData[] sprites; }
        [Serializable] public sealed class AtlasSpriteData { public string id; public RectData rect; public RectData packed_rect; public int extrusion; public bool rotated; }
        [Serializable] public sealed class EnginePropertiesData { public GodotProperties godot; public UnityProperties unity; }
        [Serializable] public sealed class GodotProperties { public string texture_filter; public string texture_repeat; public bool centered; public int z_index; }
        [Serializable] public sealed class UnityProperties { public float pixels_per_unit; public string filter_mode; public string wrap_mode; public string sorting_layer; public int sorting_order; public float z_depth; }
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
            public int UpdatedAssets;
            public int UnchangedAssets;
            public int OverridesApplied;

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
            public string Status;
            public bool OverrideApplied;
        }

        [Serializable]
        public sealed class OverridePayload
        {
            public string object_id;
            public Vector2[] polygon_in_sprite;
        }

        private sealed class OverrideData
        {
            public Vector2[] Polygon;
            public string Hash;

            public static OverrideData None() { return new OverrideData { Polygon = null, Hash = "" }; }
        }

        private sealed class ExistingSync
        {
            public bool Unchanged;

            public static ExistingSync NewAsset() { return new ExistingSync(); }
            public static ExistingSync UpdateAsset() { return new ExistingSync(); }
            public static ExistingSync UnchangedAsset() { return new ExistingSync { Unchanged = true }; }
        }

        private sealed class SyncConflictException : InvalidOperationException
        {
            public SyncConflictException(string message) : base(message) { }
        }
    }
}
