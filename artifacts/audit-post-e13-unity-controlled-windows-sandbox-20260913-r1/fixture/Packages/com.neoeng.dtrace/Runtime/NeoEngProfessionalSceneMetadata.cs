using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [DisallowMultipleComponent]
    public sealed class NeoEngProfessionalSceneMetadata : MonoBehaviour
    {
        public string sceneHash;
        public string sceneName;
        public Vector2 cameraPosition;
        public float cameraZoom;
        public string serializedGroups;
        public string serializedProject;
        public string serializedSnap;
    }

    [DisallowMultipleComponent]
    public sealed class NeoEngProfessionalLayerMetadata : MonoBehaviour
    {
        public string layerId;
        public string layerName;
        public bool visible;
        public bool locked;
        public float parallaxDepth;
        public float parallaxTranslationStrength = 1f;
        public float parallaxZoomStrength = 1f;
    }

    [DisallowMultipleComponent]
    public sealed class NeoEngProfessionalObjectMetadata : MonoBehaviour
    {
        public string objectId;
        public string assetId;
        public string layerId;
        public bool locked;
        public Vector2 pivot;
    }

    [DisallowMultipleComponent]
    public sealed class NeoEngProfessionalSocketMetadata : MonoBehaviour
    {
        public string socketId;
        public string socketType;
        public string layerId;
        public string objectId;
        public string serializedData;
    }
}
