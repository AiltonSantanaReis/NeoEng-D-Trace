using UnityEngine;

namespace NeoEng.DTrace
{
    /// <summary>
    /// Applies the authored 2D parallax contract when the imported camera moves.
    /// The component is deliberately limited to professional scene imports.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class NeoEngProfessionalParallax : MonoBehaviour
    {
        public Vector2 cameraOrigin;
        public float depth;
        public float translationStrength = 1f;
        public float zoomStrength = 1f;
        public float authoringZoom = 1f;

        private Vector3 _initialLocalPosition;
        private Vector3 _initialLocalScale;

        private void Awake()
        {
            _initialLocalPosition = transform.localPosition;
            _initialLocalScale = transform.localScale;
        }

        private void LateUpdate()
        {
            Camera camera = Camera.main;
            if (camera == null)
                return;

            float normalizedDepth = Mathf.Clamp01(depth);
            float translationFactor = 1f - normalizedDepth * Mathf.Clamp01(translationStrength);
            float zoomFactor = 1f - normalizedDepth * Mathf.Clamp01(zoomStrength);
            Vector3 delta = camera.transform.position - new Vector3(cameraOrigin.x, cameraOrigin.y, camera.transform.position.z);
            transform.localPosition = _initialLocalPosition + new Vector3(
                delta.x * (1f - translationFactor),
                delta.y * (1f - translationFactor),
                0f);

            float globalZoom = 5f / Mathf.Max(camera.orthographicSize, 0.0001f);
            float effectiveZoom = 1f + (globalZoom - 1f) * zoomFactor;
            float ratio = effectiveZoom / Mathf.Max(globalZoom, 0.0001f);
            transform.localScale = _initialLocalScale * ratio;
        }
    }
}
