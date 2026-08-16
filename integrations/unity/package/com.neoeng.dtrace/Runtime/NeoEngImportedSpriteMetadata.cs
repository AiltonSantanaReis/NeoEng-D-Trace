using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [CreateAssetMenu(menuName = "NeoEng D-Trace/Imported Sprite Metadata")]
    public sealed class NeoEngImportedSpriteMetadata : ScriptableObject
    {
        public string objectId;
        public string generatorId;
        public string generatorVersion;
        public string sourceImagePath;
        public string layerId;
        public string groupId;
        public bool trimmed;
        public int padding;
        public Rect sourceRect;
        public Vector2 pivotPixels;
        public Vector2 pivotNormalized;
        public Sprite sprite;
        public Vector2[] polygonInSprite;
    }

}
