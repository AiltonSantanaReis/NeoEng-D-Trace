using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [CreateAssetMenu(menuName = "NeoEng D-Trace/Imported Animation Metadata")]
    public sealed class NeoEngImportedAnimationMetadata : ScriptableObject
    {
        public string animationId;
        public string generatorId;
        public string generatorVersion;
        public string sourceMetadataHash;
        public string generatedFingerprint;
        public float framesPerSecond;
        public bool loop;
        public NeoEngAnimationFrame[] frames;
    }

    [Serializable]
    public sealed class NeoEngAnimationFrame
    {
        public int index;
        public Sprite sprite;
        public Vector2[] collisionPoints;
    }
}