using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using UnityEngine.Tilemaps;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class UnityOptionalResourceImporter
    {
        private const string GeneratedRoot = "Assets/NeoEngGenerated";
        private const string ConfirmDestructiveEnvironment = "NEOENG_STAGE7_CONFIRM_DESTRUCTIVE";
        private const float LegacyPixelsPerUnit = 100f;

        public static void Validate(
            UnityImportGenerator.IntegrationManifest manifest,
            string manifestPath,
            string sourceImageAssetPath,
            Texture2D sourceTexture)
        {
            if (manifest.metadata.animation != null)
            {
                ValidateAnimation(manifest.metadata.animation, manifestPath);
                foreach (UnityImportGenerator.AnimationFrameData frame in manifest.metadata.animation.frames)
                {
                    LoadTexture(frame.texture, manifestPath);
                }
            }
            if (manifest.metadata.tileset != null)
            {
                ValidateTileset(manifest.metadata.tileset, sourceTexture, manifestPath);
                foreach (UnityImportGenerator.TileData tile in manifest.metadata.tileset.tiles)
                {
                    if (!string.IsNullOrWhiteSpace(tile.texture))
                    {
                        LoadTexture(tile.texture, manifestPath);
                    }
                }
            }
        }

        public static void Import(
            UnityImportGenerator.IntegrationManifest manifest,
            string manifestPath,
            string sourceImageAssetPath,
            Texture2D sourceTexture,
            UnityImportGenerator.ImportResult result)
        {
            Validate(manifest, manifestPath, sourceImageAssetPath, sourceTexture);
            if (manifest.metadata.animation != null)
            {
                ImportAnimation(manifest, manifestPath, result);
            }
            if (manifest.metadata.tileset != null)
            {
                ImportTileset(manifest, manifestPath, sourceImageAssetPath, sourceTexture, result);
            }
        }

        private static void ImportAnimation(
            UnityImportGenerator.IntegrationManifest manifest,
            string manifestPath,
            UnityImportGenerator.ImportResult result)
        {
            UnityImportGenerator.AnimationData payload = manifest.metadata.animation;
            string id = ResourceId(manifestPath, "animation");
            string root = GeneratedRoot + "/" + id + ".animation";
            Directory.CreateDirectory(ProjectAbsolutePath(root));
            float pixelsPerUnit = PixelsPerUnit(manifest);
            List<Sprite> sprites = new List<Sprite>();
            List<Vector2[]> collisions = new List<Vector2[]>();
            string fingerprint = AnimationFingerprint(payload, manifest.source.metadata.sha256);
            string prefabPath = root + "/" + id + ".prefab";
            if (ExistingAnimationIsUnchanged(prefabPath, root, fingerprint, payload))
            {
                result.OptionalAssets.Add(new UnityImportGenerator.OptionalImportedAsset
                {
                    Kind = "animation",
                    MetadataPath = root + "/" + id + ".metadata.asset",
                    PrefabPath = prefabPath,
                    FrameCount = payload.frames.Length,
                    Status = "UNCHANGED",
                });
                result.UnchangedAssets++;
                result.ImportedAnimations++;
                return;
            }
            for (int index = 0; index < payload.frames.Length; index++)
            {
                UnityImportGenerator.AnimationFrameData frame = payload.frames[index];
                Texture2D texture = LoadTexture(frame.texture, manifestPath);
                Sprite sprite = CreateSprite(texture, frame.size, id + ".frame_" + index.ToString("D4"), pixelsPerUnit);
                string spritePath = root + "/frame_" + index.ToString("D4") + ".sprite.asset";
                ReplaceAsset(spritePath, sprite);
                sprites.Add(AssetDatabase.LoadAssetAtPath<Sprite>(spritePath));
                collisions.Add(ToUnityPoints(frame.polygon, frame.size.h, new Vector2(frame.size.w / 2f, frame.size.h / 2f), pixelsPerUnit));
            }
            string metadataPath = root + "/" + id + ".metadata.asset";
            NeoEngImportedAnimationMetadata metadata = ScriptableObject.CreateInstance<NeoEngImportedAnimationMetadata>();
            metadata.name = id + ".metadata";
            metadata.animationId = id;
            metadata.generatorId = manifest.generator.id;
            metadata.generatorVersion = manifest.generator.version;
            metadata.sourceMetadataHash = manifest.source.metadata.sha256;
            metadata.generatedFingerprint = fingerprint;
            metadata.framesPerSecond = EffectiveSpeed(payload);
            metadata.loop = payload.loop;
            metadata.frames = payload.frames.Select((frame, index) => new NeoEngAnimationFrame
            {
                index = frame.index == 0 && index > 0 ? index : frame.index,
                sprite = sprites[index],
                collisionPoints = collisions[index],
            }).ToArray();
            ReplaceAsset(metadataPath, metadata);
            metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedAnimationMetadata>(metadataPath);
            string clipPath = root + "/" + id + ".anim";
            AnimationClip clip = new AnimationClip { frameRate = metadata.framesPerSecond, wrapMode = payload.loop ? WrapMode.Loop : WrapMode.Default };
            ObjectReferenceKeyframe[] keys = metadata.frames.Select((frame, index) => new ObjectReferenceKeyframe
            {
                time = index / metadata.framesPerSecond,
                value = frame.sprite,
            }).ToArray();
            AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"), keys);
            ReplaceAsset(clipPath, clip);
            clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
            string controllerPath = root + "/" + id + ".controller";
            if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(controllerPath) != null) AssetDatabase.DeleteAsset(controllerPath);
            AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            AnimatorState state = controller.layers[0].stateMachine.AddState(id);
            state.motion = clip;
            AssetDatabase.SaveAssets();
            GameObject rootObject = new GameObject(id);
            SpriteRenderer renderer = rootObject.AddComponent<SpriteRenderer>();
            renderer.sprite = sprites[0];
            Animator animator = rootObject.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            PolygonCollider2D collider = rootObject.AddComponent<PolygonCollider2D>();
            collider.pathCount = 1;
            collider.SetPath(0, collisions[0]);
            NeoEngAnimationCollisionDriver driver = rootObject.AddComponent<NeoEngAnimationCollisionDriver>();
            driver.metadata = metadata;
            NeoEngGeneratedMarker marker = rootObject.AddComponent<NeoEngGeneratedMarker>();
            marker.generatorId = manifest.generator.id;
            marker.generatorVersion = manifest.generator.version;
            marker.objectId = id;
            marker.sourceImageHash = manifest.source.image.sha256;
            marker.sourceMetadataHash = manifest.source.metadata.sha256;
            marker.generatedFingerprint = fingerprint;
            SavePrefab(rootObject, prefabPath);
            UnityEngine.Object.DestroyImmediate(rootObject);
            result.OptionalAssets.Add(new UnityImportGenerator.OptionalImportedAsset
            {
                Kind = "animation",
                MetadataPath = metadataPath,
                PrefabPath = prefabPath,
                FrameCount = payload.frames.Length,
                Status = "UPDATED",
            });
            result.ImportedAnimations++;
            result.UpdatedAssets++;
        }

        private static void ImportTileset(
            UnityImportGenerator.IntegrationManifest manifest,
            string manifestPath,
            string sourceImageAssetPath,
            Texture2D sourceTexture,
            UnityImportGenerator.ImportResult result)
        {
            UnityImportGenerator.TilesetData payload = manifest.metadata.tileset;
            string id = ResourceId(manifestPath, "tileset");
            string root = GeneratedRoot + "/" + id + ".tileset";
            Directory.CreateDirectory(ProjectAbsolutePath(root));
            string fingerprint = TilesetFingerprint(payload, manifest.source.image.sha256, manifest.source.metadata.sha256);
            string prefabPath = root + "/" + id + ".prefab";
            if (ExistingTilesetIsUnchanged(prefabPath, fingerprint, payload, manifest))
            {
                result.OptionalAssets.Add(new UnityImportGenerator.OptionalImportedAsset
                {
                    Kind = "tileset",
                    MetadataPath = root + "/" + id + ".metadata.asset",
                    PrefabPath = prefabPath,
                    TileCount = payload.tiles.Length,
                    Status = "UNCHANGED",
                });
                result.UnchangedAssets++;
                result.ImportedTilesets++;
                return;
            }
            List<NeoEngTilesetTile> tileRecords = new List<NeoEngTilesetTile>();
            List<Vector2[]> compoundCollisions = new List<Vector2[]>();
            GameObject gridObject = new GameObject(id);
            Grid grid = gridObject.AddComponent<Grid>();
            float pixelsPerUnit = PixelsPerUnit(manifest);
            grid.cellSize = new Vector3(payload.tile_size.w / pixelsPerUnit, payload.tile_size.h / pixelsPerUnit, 1f);
            GameObject tilemapObject = new GameObject("Tilemap");
            tilemapObject.transform.SetParent(gridObject.transform, false);
            Tilemap tilemap = tilemapObject.AddComponent<Tilemap>();
            tilemapObject.AddComponent<TilemapRenderer>();
            for (int index = 0; index < payload.tiles.Length; index++)
            {
                UnityImportGenerator.TileData tileData = payload.tiles[index];
                Texture2D texture = string.IsNullOrWhiteSpace(tileData.texture)
                    ? sourceTexture
                    : LoadTexture(tileData.texture, manifestPath);
                Sprite sprite = CreateSprite(texture, tileData.source_rect, id + ".tile_" + index.ToString("D4"), pixelsPerUnit);
                Vector2[] collision = tileData.collision == null
                    ? Array.Empty<Vector2>()
                    : ToUnityPoints(tileData.collision, tileData.source_rect.h, new Vector2(tileData.source_rect.w / 2f, tileData.source_rect.h / 2f), pixelsPerUnit);
                if (collision.Length > 0)
                {
                    Vector2 tileCenter = new Vector2(
                        (tileData.column + 0.5f) * grid.cellSize.x,
                        -(tileData.row + 0.5f) * grid.cellSize.y);
                    compoundCollisions.Add(collision.Select(point => point + tileCenter).ToArray());
                }
                string spritePath = root + "/tile_" + index.ToString("D4") + ".sprite.asset";
                ReplaceAsset(spritePath, sprite);
                sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
                Tile tile = ScriptableObject.CreateInstance<Tile>();
                tile.name = tileData.id + ".tile";
                tile.sprite = sprite;
                tile.colliderType = Tile.ColliderType.None;
                string tilePath = root + "/" + SafeName(tileData.id) + ".tile.asset";
                ReplaceAsset(tilePath, tile);
                tile = AssetDatabase.LoadAssetAtPath<Tile>(tilePath);
                tilemap.SetTile(new Vector3Int(tileData.column, tileData.row, 0), tile);
                tileRecords.Add(new NeoEngTilesetTile
                {
                    id = tileData.id,
                    index = tileData.index,
                    row = tileData.row,
                    column = tileData.column,
                    tile = tile,
                    collisionPoints = collision,
                });
            }
            if (compoundCollisions.Count > 0)
            {
                PolygonCollider2D compoundCollider = gridObject.AddComponent<PolygonCollider2D>();
                compoundCollider.pathCount = compoundCollisions.Count;
                for (int index = 0; index < compoundCollisions.Count; index++)
                {
                    compoundCollider.SetPath(index, compoundCollisions[index]);
                }
            }            string metadataPath = root + "/" + id + ".metadata.asset";
            NeoEngImportedTilesetMetadata metadata = ScriptableObject.CreateInstance<NeoEngImportedTilesetMetadata>();
            metadata.name = id + ".metadata";
            metadata.tilesetId = id;
            metadata.generatorId = manifest.generator.id;
            metadata.generatorVersion = manifest.generator.version;
            metadata.sourceImageHash = manifest.source.image.sha256;
            metadata.sourceMetadataHash = manifest.source.metadata.sha256;
            metadata.generatedFingerprint = fingerprint;
            metadata.tileSize = new Vector2Int(payload.tile_size.w, payload.tile_size.h);
            metadata.spacing = payload.spacing;
            metadata.margin = payload.margin;
            metadata.tiles = tileRecords.ToArray();
            ReplaceAsset(metadataPath, metadata);
            metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedTilesetMetadata>(metadataPath);
            NeoEngGeneratedMarker marker = gridObject.AddComponent<NeoEngGeneratedMarker>();
            marker.generatorId = manifest.generator.id;
            marker.generatorVersion = manifest.generator.version;
            marker.objectId = id;
            marker.sourceImageHash = manifest.source.image.sha256;
            marker.sourceMetadataHash = manifest.source.metadata.sha256;
            marker.generatedFingerprint = fingerprint;
            SavePrefab(gridObject, prefabPath);
            UnityEngine.Object.DestroyImmediate(gridObject);
            result.OptionalAssets.Add(new UnityImportGenerator.OptionalImportedAsset
            {
                Kind = "tileset",
                MetadataPath = metadataPath,
                PrefabPath = prefabPath,
                TileCount = payload.tiles.Length,
                Status = "UPDATED",
            });
            result.ImportedTilesets++;
            result.UpdatedAssets++;
        }

        private static bool ExistingAnimationIsUnchanged(
            string prefabPath,
            string root,
            string expectedFingerprint,
            UnityImportGenerator.AnimationData payload)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null) return false;
            NeoEngGeneratedMarker marker = prefab.GetComponent<NeoEngGeneratedMarker>();
            string id = Path.GetFileName(root).Replace(".animation", "", StringComparison.Ordinal);
            NeoEngImportedAnimationMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedAnimationMetadata>(root + "/" + id + ".metadata.asset");
            PolygonCollider2D collider = prefab.GetComponent<PolygonCollider2D>();
            if (marker == null || metadata == null || collider == null || marker.generatedFingerprint != expectedFingerprint || metadata.generatedFingerprint != expectedFingerprint || metadata.frames == null || metadata.frames.Length != payload.frames.Length || collider.pathCount != 1 || !SamePoints(collider.GetPath(0), metadata.frames[0].collisionPoints))
            {
                ThrowConflict(prefabPath);
            }
            return true;
        }

        private static bool ExistingTilesetIsUnchanged(string prefabPath, string expectedFingerprint, UnityImportGenerator.TilesetData payload, UnityImportGenerator.IntegrationManifest manifest)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null) return false;
            NeoEngGeneratedMarker marker = prefab.GetComponent<NeoEngGeneratedMarker>();
            Tilemap tilemap = prefab.GetComponentInChildren<Tilemap>();
            PolygonCollider2D collider = prefab.GetComponent<PolygonCollider2D>();
            List<Vector2[]> expectedPaths = TilesetCollisionPaths(payload, manifest);
            if (marker == null || tilemap == null || collider == null || marker.generatedFingerprint != expectedFingerprint || UsedTileCount(tilemap) != payload.tiles.Length || collider.pathCount != expectedPaths.Count || expectedPaths.Where((path, index) => !SamePoints(collider.GetPath(index), path)).Any())
            {
                ThrowConflict(prefabPath);
            }
            return true;
        }

        private static List<Vector2[]> TilesetCollisionPaths(UnityImportGenerator.TilesetData payload, UnityImportGenerator.IntegrationManifest manifest)
        {
            float pixelsPerUnit = PixelsPerUnit(manifest);
            Vector2 cellSize = new Vector2(payload.tile_size.w / pixelsPerUnit, payload.tile_size.h / pixelsPerUnit);
            return payload.tiles.Where(tile => tile.collision != null && tile.collision.Length >= 3).Select(tile =>
            {
                Vector2[] local = ToUnityPoints(tile.collision, tile.source_rect.h, new Vector2(tile.source_rect.w / 2f, tile.source_rect.h / 2f), pixelsPerUnit);
                Vector2 center = new Vector2((tile.column + 0.5f) * cellSize.x, -(tile.row + 0.5f) * cellSize.y);
                return local.Select(point => point + center).ToArray();
            }).ToList();
        }
        private static int UsedTileCount(Tilemap tilemap)
        {
            return tilemap.GetTilesBlock(tilemap.cellBounds).Count(tile => tile != null);
        }

        private static void ThrowConflict(string path)
        {
            if (!IsDestructiveConfirmed())
            {
                throw new UnityImportGenerator.SyncConflictException("generated Unity optional output was manually modified: " + path);
            }
        }

        private static bool IsDestructiveConfirmed()
        {
            string value = Environment.GetEnvironmentVariable(ConfirmDestructiveEnvironment);
            return string.Equals(value, "1", StringComparison.OrdinalIgnoreCase) || string.Equals(value, "true", StringComparison.OrdinalIgnoreCase);
        }

        private static void ValidateAnimation(UnityImportGenerator.AnimationData payload, string manifestPath)
        {
            if (payload.format_id != "neoeng-d-trace-animation" || payload.schema_version != 1 || payload.frames == null || payload.frames.Length == 0 || payload.frame_count != payload.frames.Length)
            {
                throw new InvalidDataException("Unity animation payload is invalid");
            }
            if (payload.speed < 0f || float.IsNaN(payload.speed) || float.IsInfinity(payload.speed))
            {
                throw new InvalidDataException("Unity animation speed is invalid");
            }
            foreach (UnityImportGenerator.AnimationFrameData frame in payload.frames)
            {
                if (frame == null || frame.size == null || frame.size.w <= 0 || frame.size.h <= 0 || frame.polygon == null || frame.polygon.Length < 3)
                {
                    throw new InvalidDataException("Unity animation frame geometry is invalid");
                }
                ValidatePath(frame.polygon, "animation frame");
            }
        }

        private static void ValidateTileset(UnityImportGenerator.TilesetData payload, Texture2D sourceTexture, string manifestPath)
        {
            if (payload.format_id != "neoeng-d-trace-tileset" || payload.schema_version != 1 || payload.tile_size == null || payload.tile_size.w <= 0 || payload.tile_size.h <= 0 || payload.spacing < 0 || payload.margin < 0 || payload.tiles == null || payload.tiles.Length == 0)
            {
                throw new InvalidDataException("Unity tileset payload is invalid");
            }
            foreach (UnityImportGenerator.TileData tile in payload.tiles)
            {
                if (tile == null || string.IsNullOrWhiteSpace(tile.id) || tile.source_rect == null || tile.source_rect.w <= 0 || tile.source_rect.h <= 0 || tile.source_rect.x < 0 || tile.source_rect.y < 0 || tile.source_rect.x + tile.source_rect.w > sourceTexture.width || tile.source_rect.y + tile.source_rect.h > sourceTexture.height)
                {
                    throw new InvalidDataException("Unity tileset tile geometry is invalid");
                }
                if (tile.collision != null) ValidatePath(tile.collision, "tileset collision");
            }
        }

        private static void ValidatePath(Vector2[] points, string field)
        {
            if (points == null || points.Length < 3 || points.Any(point => float.IsNaN(point.x) || float.IsNaN(point.y) || float.IsInfinity(point.x) || float.IsInfinity(point.y)))
            {
                throw new InvalidDataException(field + " must contain finite polygon points");
            }
        }

        private static Texture2D LoadTexture(string reference, string manifestPath)
        {
            string assetPath = ToAssetPath(reference);
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
            Texture2D texture = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
            if (texture == null) throw new InvalidDataException("Unity optional texture could not be loaded: " + assetPath);
            return texture;
        }

        private static string ToAssetPath(string reference)
        {
            if (string.IsNullOrWhiteSpace(reference) || reference.Contains("\\") || reference.StartsWith("/", StringComparison.Ordinal) || reference.Contains(":") || reference.Split('/').Contains(".."))
            {
                throw new InvalidDataException("Unity optional texture path is unsafe");
            }
            string normalized = reference.TrimStart('.', '/');
            return normalized.StartsWith("Assets/", StringComparison.Ordinal) ? normalized : "Assets/" + normalized;
        }

        private static Sprite CreateSprite(Texture2D texture, UnityImportGenerator.SizeData size, string name, float pixelsPerUnit)
        {
            return Sprite.Create(texture, new Rect(0f, 0f, size.w, size.h), new Vector2(0.5f, 0.5f), pixelsPerUnit, 0, SpriteMeshType.FullRect);
        }

        private static Sprite CreateSprite(Texture2D texture, UnityImportGenerator.RectData rect, string name, float pixelsPerUnit)
        {
            Rect source = new Rect(rect.x, texture.height - rect.y - rect.h, rect.w, rect.h);
            return Sprite.Create(texture, source, new Vector2(0.5f, 0.5f), pixelsPerUnit, 0, SpriteMeshType.Tight);
        }

        private static Vector2[] ToUnityPoints(Vector2[] points, float height, Vector2 pivot, float pixelsPerUnit)
        {
            ValidatePath(points, "optional collision");
            return points.Select(point => new Vector2((point.x - pivot.x) / pixelsPerUnit, (height - point.y - pivot.y) / pixelsPerUnit)).ToArray();
        }

        private static void ReplaceAsset(string assetPath, UnityEngine.Object asset)
        {
            if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(assetPath) != null) AssetDatabase.DeleteAsset(assetPath);
            AssetDatabase.CreateAsset(asset, assetPath);
        }

        private static void SavePrefab(GameObject root, string prefabPath)
        {
            if (AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) != null) AssetDatabase.DeleteAsset(prefabPath);
            if (PrefabUtility.SaveAsPrefabAsset(root, prefabPath) == null) throw new InvalidOperationException("Unity optional prefab could not be saved");
        }

        private static string ResourceId(string manifestPath, string suffix)
        {
            string name = Path.GetFileNameWithoutExtension(manifestPath);
            if (name.EndsWith(".ndt.integration", StringComparison.OrdinalIgnoreCase)) name = name.Substring(0, name.Length - ".ndt.integration".Length);
            return SafeName(name + "_" + suffix);
        }

        private static string SafeName(string value)
        {
            if (string.IsNullOrWhiteSpace(value) || value.Any(character => !(char.IsLetterOrDigit(character) || character == '_' || character == '-'))) throw new InvalidDataException("Unity optional resource id is unsafe");
            return value;
        }

        private static float PixelsPerUnit(UnityImportGenerator.IntegrationManifest manifest)
        {
            return manifest.schema_version == 2 ? manifest.advanced.engine_properties.unity.pixels_per_unit : LegacyPixelsPerUnit;
        }

        private static float EffectiveSpeed(UnityImportGenerator.AnimationData payload)
        {
            return payload.speed == 0f ? 12f : payload.speed;
        }

        private static string AnimationFingerprint(UnityImportGenerator.AnimationData payload, string metadataHash)
        {
            string signature = metadataHash + "|" + EffectiveSpeed(payload).ToString("R", CultureInfo.InvariantCulture) + "|" + payload.loop + "|" + string.Join("|", payload.frames.Select(frame => string.Join(";", frame.polygon.Select(FormatPoint))));
            return Hash(signature);
        }

        private static string TilesetFingerprint(UnityImportGenerator.TilesetData payload, string imageHash, string metadataHash)
        {
            string signature = imageHash + "|" + metadataHash + "|" + string.Join("|", payload.tiles.Select(tile => tile.id + ":" + tile.row + ":" + tile.column + ":" + string.Join(";", (tile.collision ?? Array.Empty<Vector2>()).Select(FormatPoint))));
            return Hash(signature);
        }

        private static string FormatPoint(Vector2 point)
        {
            return Math.Round(point.x, 6).ToString("0.######", CultureInfo.InvariantCulture) + "," + Math.Round(point.y, 6).ToString("0.######", CultureInfo.InvariantCulture);
        }

        private static bool SamePoints(Vector2[] left, Vector2[] right)
        {
            return left != null && right != null && left.Length == right.Length && left.Zip(right, (a, b) => Math.Abs(a.x - b.x) < 0.0001f && Math.Abs(a.y - b.y) < 0.0001f).All(value => value);
        }

        private static string Hash(string value)
        {
            using (SHA256 sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value))).Replace("-", "").ToLowerInvariant();
        }

        private static string ProjectAbsolutePath(string assetPath)
        {
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string relative = assetPath.StartsWith("Assets/", StringComparison.Ordinal) ? assetPath.Substring("Assets/".Length) : assetPath;
            return Path.Combine(Application.dataPath, relative.Replace('/', Path.DirectorySeparatorChar));
        }
    }
}