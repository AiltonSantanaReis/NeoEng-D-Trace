using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class EngineExportValidator
{
    [Serializable]
    private sealed class RectRecord
    {
        public float x;
        public float y;
        public float width;
        public float height;
    }

    [Serializable]
    private sealed class PointRecord
    {
        public float x;
        public float y;
    }

    [Serializable]
    private sealed class CollisionRecord
    {
        public string shape_type;
    }

    [Serializable]
    private sealed class MetadataRecord
    {
        public string schema;
        public int schema_version;
        public string name;
        public RectRecord rect;
        public PointRecord pivot;
        public CollisionRecord collision;
    }

    [Serializable]
    private sealed class SceneMetadataRecord
    {
        public MetadataRecord[] sprites;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidDataException(message);
        }
    }

    public static void Run()
    {
        try
        {
            var metadataText = File.ReadAllText("Assets/probe-unity.json");
            var sceneMetadata = JsonUtility.FromJson<SceneMetadataRecord>(metadataText);
            var metadata =
                sceneMetadata != null
                && sceneMetadata.sprites != null
                && sceneMetadata.sprites.Length == 1
                    ? sceneMetadata.sprites[0]
                    : JsonUtility.FromJson<MetadataRecord>(metadataText);
            Require(metadata != null, "metadata-json");
            Require(metadata.schema == "neoeng-d-trace-unity-sprite", "metadata-schema");
            Require(metadata.schema_version == 1, "metadata-version");
            Require(metadata.name == "sprite_ação", "metadata-unicode-name");
            Require(metadata.collision != null, "collision-missing");
            Require(metadata.collision.shape_type == "polygon", "collision-schema");

            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/source.png");
            Require(texture != null, "texture-import");
            var unityRect = new Rect(
                metadata.rect.x,
                texture.height - metadata.rect.y - metadata.rect.height,
                metadata.rect.width,
                metadata.rect.height
            );
            var unityPivot = new Vector2(metadata.pivot.x, 1.0f - metadata.pivot.y);
            var sprite = Sprite.Create(texture, unityRect, unityPivot, 100.0f);
            Require(sprite != null, "sprite-create");
            Require(sprite.rect.width == 40.0f && sprite.rect.height == 20.0f, "sprite-rect");
            Require(sprite.pivot == new Vector2(20.0f, 10.0f), "sprite-pivot");

            var imported = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/scene.glb");
            Require(imported != null, "glb-import");

            File.WriteAllText(
                "engine-validation-result.txt",
                "ENGINE_VALIDATION=SUCCESS\nENGINE_VERSION=" + Application.unityVersion + "\n"
            );
            UnityEngine.Object.DestroyImmediate(sprite);
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            File.WriteAllText(
                "engine-validation-result.txt",
                "ENGINE_VALIDATION=FAILED\nREASON=" + exception.Message + "\n"
            );
            Debug.LogException(exception);
            EditorApplication.Exit(1);
        }
    }
}
