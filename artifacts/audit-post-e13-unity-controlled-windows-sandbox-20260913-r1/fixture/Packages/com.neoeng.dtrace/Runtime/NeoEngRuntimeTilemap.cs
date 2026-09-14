using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace NeoEng.DTrace
{
    /// <summary>
    /// Materializes the v1 authored tilemap payload with native Unity
    /// SpriteRenderers.  Source and atlas bindings are checked before any
    /// runtime objects are created, so asset drift fails closed.
    /// </summary>
    public static class NeoEngRuntimeTilemap
    {
        private const string FormatId = "neoeng-d-trace-tilemap-runtime";
        private const int SchemaVersion = 1;

        [Serializable]
        public sealed class SourceData
        {
            public string path;
            public string sha256;
            public long bytes;
        }

        [Serializable]
        public sealed class AtlasData
        {
            public string path;
            public string sha256;
            public long bytes;
        }

        [Serializable]
        public sealed class RectData
        {
            public int x;
            public int y;
            public int w;
            public int h;
        }

        [Serializable]
        public sealed class PivotData
        {
            public float x;
            public float y;
        }

        [Serializable]
        public sealed class TileData
        {
            public string id;
            public string asset_id;
            public RectData source_rect;
            public PivotData pivot;
            public string variant;
            public string[] animation_frames;
            public int version;
        }

        [Serializable]
        public sealed class TilesetData
        {
            public string id;
            public string atlas_asset_id;
            public string atlas_sha256;
            public int version;
            public TileData[] tiles;
        }

        [Serializable]
        public sealed class LayerData
        {
            public string id;
            public string name;
            public int order;
            public bool visible;
            public bool locked;
            public float opacity;
        }

        [Serializable]
        public sealed class CellData
        {
            public string layer_id;
            public int x;
            public int y;
            public string tile_id;
            public string variant;
        }

        [Serializable]
        public sealed class RuleData
        {
            public string id;
            public string target_tile_id;
        }

        [Serializable]
        public sealed class RulesData
        {
            public string fallback_tile_id;
            public RuleData[] rules;
        }

        [Serializable]
        public sealed class CountsData
        {
            public int layers;
            public int tiles;
            public int cells;
            public int rules;
        }

        [Serializable]
        public sealed class PayloadData
        {
            public string format_id;
            public int schema_version;
            public SourceData source;
            public string id;
            public string name;
            public string grid;
            public int chunk_size;
            public TilesetData tileset;
            public AtlasData atlas;
            public LayerData[] layers;
            public CellData[] cells;
            public RulesData rules;
            public CountsData counts;
        }

        public sealed class Result
        {
            public GameObject Root { get; internal set; }
            public PayloadData Payload { get; internal set; }
            public int Layers { get; internal set; }
            public int Tiles { get; internal set; }
            public int TileCells { get; internal set; }
            public int RenderedSprites { get; internal set; }
            public int Rules { get; internal set; }
            public string AtlasPath { get; internal set; }
            public string AtlasSha256 { get; internal set; }
        }

        public static Result Import(string payloadPath)
        {
            if (string.IsNullOrWhiteSpace(payloadPath))
                throw new InvalidDataException("tilemap runtime payload path is empty");
            string fullPayloadPath = Path.GetFullPath(payloadPath);
            if (!File.Exists(fullPayloadPath))
                throw new FileNotFoundException("tilemap runtime payload was not found", fullPayloadPath);
            string baseDirectory = Path.GetDirectoryName(fullPayloadPath);
            string json = File.ReadAllText(fullPayloadPath, Encoding.UTF8);
            PayloadData payload = JsonUtility.FromJson<PayloadData>(json);
            Validate(payload, baseDirectory);

            string atlasPath = ResolveSafeReference(baseDirectory, payload.atlas.path, "atlas.path");
            byte[] atlasBytes = File.ReadAllBytes(atlasPath);
            Texture2D atlas = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            if (!atlas.LoadImage(atlasBytes, false))
                throw new InvalidDataException("tilemap atlas could not be decoded by Unity");

            Dictionary<string, TileData> tiles = payload.tileset.tiles
                .ToDictionary(item => item.id, StringComparer.Ordinal);
            Dictionary<string, GameObject> layers = new Dictionary<string, GameObject>(StringComparer.Ordinal);
            GameObject root = new GameObject("NeoEngRuntimeTilemap");
            foreach (LayerData layer in payload.layers.OrderBy(item => item.order).ThenBy(item => item.id, StringComparer.Ordinal))
            {
                GameObject layerObject = new GameObject("TileLayer_" + layer.id);
                layerObject.transform.SetParent(root.transform, false);
                layerObject.SetActive(layer.visible);
                layerObject.transform.localScale = Vector3.one;
                layers.Add(layer.id, layerObject);
            }

            int renderedSprites = 0;
            foreach (CellData cell in payload.cells)
            {
                TileData tile = tiles[cell.tile_id];
                RectData rect = tile.source_rect;
                if (rect.x < 0 || rect.y < 0 || rect.w <= 0 || rect.h <= 0
                    || rect.x + rect.w > atlas.width || rect.y + rect.h > atlas.height)
                    throw new InvalidDataException("tile source rectangle is outside the runtime atlas");
                Sprite sprite = Sprite.Create(
                    atlas,
                    new Rect(rect.x, atlas.height - rect.y - rect.h, rect.w, rect.h),
                    new Vector2(0.0f, 1.0f),
                    1.0f);
                GameObject tileObject = new GameObject("Tile_" + cell.tile_id + "_" + cell.x + "_" + cell.y);
                tileObject.transform.SetParent(layers[cell.layer_id].transform, false);
                tileObject.transform.localPosition = CellPosition(payload.grid, cell.x, cell.y, rect);
                SpriteRenderer renderer = tileObject.AddComponent<SpriteRenderer>();
                renderer.sprite = sprite;
                renderer.sortingOrder = payload.layers.First(item => item.id == cell.layer_id).order;
                renderedSprites++;
            }

            return new Result
            {
                Root = root,
                Payload = payload,
                Layers = payload.layers.Length,
                Tiles = payload.tileset.tiles.Length,
                TileCells = payload.cells.Length,
                RenderedSprites = renderedSprites,
                Rules = payload.rules.rules.Length,
                AtlasPath = atlasPath,
                AtlasSha256 = payload.atlas.sha256,
            };
        }

        private static Vector3 CellPosition(string grid, int x, int y, RectData rect)
        {
            float width = rect.w;
            float height = rect.h;
            if (grid == "isometric")
                return new Vector3((x - y) * width * 0.5f, (x + y) * height * 0.5f, 0.0f);
            if (grid == "hexagonal")
                return new Vector3(x * width * 0.75f, y * height + (Mathf.Abs(x) % 2) * height * 0.5f, 0.0f);
            return new Vector3(x * width, -y * height, 0.0f);
        }

        private static void Validate(PayloadData payload, string baseDirectory)
        {
            if (payload == null || payload.format_id != FormatId || payload.schema_version != SchemaVersion)
                throw new InvalidDataException("unsupported tilemap runtime payload");
            if (payload.source == null || payload.atlas == null || payload.tileset == null
                || payload.layers == null || payload.cells == null || payload.rules == null || payload.counts == null)
                throw new InvalidDataException("tilemap runtime payload is incomplete");
            if (payload.grid != "orthogonal" && payload.grid != "isometric" && payload.grid != "hexagonal")
                throw new InvalidDataException("tilemap runtime grid is unsupported");
            ValidateBinding(baseDirectory, payload.source.path, payload.source.sha256, payload.source.bytes, "source");
            ValidateBinding(baseDirectory, payload.atlas.path, payload.atlas.sha256, payload.atlas.bytes, "atlas");
            if (payload.tileset.tiles == null || payload.tileset.tiles.Length == 0
                || payload.tileset.atlas_sha256 != payload.atlas.sha256)
                throw new InvalidDataException("tilemap runtime tileset binding is invalid");
            HashSet<string> tileIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (TileData tile in payload.tileset.tiles)
            {
                if (tile == null || string.IsNullOrWhiteSpace(tile.id) || !tileIds.Add(tile.id)
                    || tile.source_rect == null || tile.source_rect.x < 0 || tile.source_rect.y < 0
                    || tile.source_rect.w <= 0 || tile.source_rect.h <= 0)
                    throw new InvalidDataException("tilemap runtime tile definitions are invalid");
            }
            HashSet<string> layerIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (LayerData layer in payload.layers)
            {
                if (layer == null || string.IsNullOrWhiteSpace(layer.id) || !layerIds.Add(layer.id)
                    || string.IsNullOrWhiteSpace(layer.name) || layer.opacity < 0.0f || layer.opacity > 1.0f)
                    throw new InvalidDataException("tilemap runtime layer definitions are invalid");
            }
            HashSet<string> cellKeys = new HashSet<string>(StringComparer.Ordinal);
            foreach (CellData cell in payload.cells)
            {
                if (cell == null || !layerIds.Contains(cell.layer_id) || !tileIds.Contains(cell.tile_id)
                    || !cellKeys.Add(cell.layer_id + ":" + cell.x + ":" + cell.y))
                    throw new InvalidDataException("tilemap runtime cell references are invalid");
            }
            if (!tileIds.Contains(payload.rules.fallback_tile_id) || payload.rules.rules == null)
                throw new InvalidDataException("tilemap runtime rules are invalid");
            foreach (RuleData rule in payload.rules.rules)
            {
                if (rule == null || string.IsNullOrWhiteSpace(rule.id) || !tileIds.Contains(rule.target_tile_id))
                    throw new InvalidDataException("tilemap runtime rule targets are invalid");
            }
            if (payload.counts.layers != payload.layers.Length || payload.counts.tiles != payload.tileset.tiles.Length
                || payload.counts.cells != payload.cells.Length || payload.counts.rules != payload.rules.rules.Length)
                throw new InvalidDataException("tilemap runtime counts are inconsistent");
        }

        private static void ValidateBinding(string baseDirectory, string relativePath, string expectedSha, long expectedBytes, string label)
        {
            string fullPath = ResolveSafeReference(baseDirectory, relativePath, label + ".path");
            byte[] bytes = File.ReadAllBytes(fullPath);
            if (expectedBytes >= 0 && bytes.LongLength != expectedBytes)
                throw new InvalidDataException(label + " file size mismatch");
            if (!string.Equals(Sha256(bytes), expectedSha, StringComparison.Ordinal))
                throw new InvalidDataException(label + " file hash mismatch");
        }

        private static string ResolveSafeReference(string baseDirectory, string relativePath, string label)
        {
            if (string.IsNullOrWhiteSpace(relativePath) || relativePath.Contains("\\") || relativePath.Contains(":") || Path.IsPathRooted(relativePath))
                throw new InvalidDataException(label + " must be a safe relative path");
            string[] parts = relativePath.Split('/');
            if (parts.Any(part => string.IsNullOrEmpty(part) || part == "." || part == ".."))
                throw new InvalidDataException(label + " must be a safe relative path");
            string root = Path.GetFullPath(baseDirectory).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string fullPath = Path.GetFullPath(Path.Combine(root, relativePath.Replace('/', Path.DirectorySeparatorChar)));
            if (!fullPath.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(label + " resolves outside the payload directory");
            if (!File.Exists(fullPath))
                throw new FileNotFoundException(label + " file does not exist", fullPath);
            return fullPath;
        }

        private static string Sha256(byte[] bytes)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", string.Empty).ToLowerInvariant();
        }
    }
}
