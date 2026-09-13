using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    public sealed class NeoEngAnimationCollisionDriver : MonoBehaviour
    {
        public NeoEngImportedAnimationMetadata metadata;

        private SpriteRenderer spriteRenderer;
        private Component polygonCollider;
        private Sprite lastSprite;
        private Type polygonColliderType;

        private void Awake()
        {
            spriteRenderer = GetComponent<SpriteRenderer>();
            ResolveCollider();
            SyncCollision();
        }

        private void LateUpdate()
        {
            if (spriteRenderer != null && spriteRenderer.sprite != lastSprite)
            {
                SyncCollision();
            }
        }

        public void SyncCollision()
        {
            if (spriteRenderer == null)
            {
                spriteRenderer = GetComponent<SpriteRenderer>();
            }
            ResolveCollider();
            if (metadata == null || spriteRenderer == null || polygonCollider == null)
            {
                return;
            }
            for (int index = 0; index < (metadata.frames == null ? 0 : metadata.frames.Length); index++)
            {
                NeoEngAnimationFrame frame = metadata.frames[index];
                if (frame != null && frame.sprite == spriteRenderer.sprite && frame.collisionPoints != null)
                {
                    polygonColliderType.GetProperty("pathCount").SetValue(polygonCollider, 1, null);
                    polygonColliderType.GetMethod("SetPath", new[] { typeof(int), typeof(Vector2[]) }).Invoke(polygonCollider, new object[] { 0, frame.collisionPoints });
                    lastSprite = spriteRenderer.sprite;
                    return;
                }
            }
            lastSprite = spriteRenderer.sprite;
        }

        private void ResolveCollider()
        {
            if (polygonCollider != null)
            {
                return;
            }
            polygonColliderType = Type.GetType("UnityEngine.PolygonCollider2D, UnityEngine.Physics2DModule");
            if (polygonColliderType != null)
            {
                polygonCollider = GetComponent(polygonColliderType);
            }
        }
    }
}