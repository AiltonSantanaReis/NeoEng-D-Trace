using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [CreateAssetMenu(menuName = "NeoEng D-Trace/Imported Tileset Metadata")]
    public sealed class NeoEngImportedTilesetMetadata : ScriptableObject
    {
        public string tilesetId;
        public string generatorId;
        public string generatorVersion;
        public string sourceImageHash;
        public string sourceMetadataHash;
        public string generatedFingerprint;
        public Vector2Int tileSize;
        public int spacing;
        public int margin;
        public NeoEngTilesetTile[] tiles;
    }

    [Serializable]
    public sealed class NeoEngTilesetTile
    {
        public string id;
        public int index;
        public int row;
        public int column;
        public ScriptableObject tile;
        public Vector2[] collisionPoints;
    }
}