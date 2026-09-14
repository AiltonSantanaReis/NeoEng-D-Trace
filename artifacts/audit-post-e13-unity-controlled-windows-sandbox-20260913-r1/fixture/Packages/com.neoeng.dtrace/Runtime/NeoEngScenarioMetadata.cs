using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [DisallowMultipleComponent]
    public sealed class NeoEngScenarioMetadata : MonoBehaviour
    {
        public string scenarioHash;
        public string projectHash;
        public Vector2 cameraPosition;
        public float cameraZoom;
    }

    [DisallowMultipleComponent]
    public sealed class NeoEngScenarioLayerMetadata : MonoBehaviour
    {
        public string layerId;
        public string layerName;
        public bool visible;
        public string[] objectIds = Array.Empty<string>();
        public float parallaxDepth;
        public float parallaxTranslationStrength;
        public float parallaxZoomStrength;
    }
}
