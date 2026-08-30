using System;
using System.IO;
using NeoEng.DTrace;
using UnityEditor;
using UnityEngine;

namespace NeoEng.DTrace.Editor
{
    public static class ProfessionalSceneValidation
    {
        private static void Require(bool condition, string message)
        {
            if (!condition)
                throw new InvalidDataException(message);
        }

        public static void Run()
        {
            try
            {
                const string assetPath = "Assets/assets/hero.png";
                TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                Require(importer != null, "unity-texture-importer");
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.SaveAndReimport();
                AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceSynchronousImport);

                GameObject root = ProfessionalSceneImportGenerator.Import(
                    "Assets/NeoEngGenerated/scene-authoring.unity.json");
                Transform cameraTransform = root.transform.Find("SceneCamera");
                Require(cameraTransform != null, "unity-camera-materialization");
                Camera camera = cameraTransform.GetComponent<Camera>();
                Require(camera != null && camera.orthographic, "unity-camera-component");
                Require(Mathf.Abs(cameraTransform.localPosition.x - 0.8f) < 0.0001f, "unity-camera-x");
                Require(Mathf.Abs(cameraTransform.localPosition.y + 0.4f) < 0.0001f, "unity-camera-y-mapping");

                Transform layer = root.transform.Find("Layer_foreground");
                Require(layer != null, "unity-layer-materialization");
                Require(layer.GetComponent<NeoEngProfessionalParallax>() != null, "unity-parallax-materialization");
                Transform instance = layer.Find("Object_hero");
                Require(instance != null, "unity-object-materialization");
                Require(Mathf.Abs(instance.localPosition.x - 0.8f) < 0.0001f, "unity-object-x");
                Require(Mathf.Abs(instance.localPosition.y + 0.4f) < 0.0001f, "unity-object-y-mapping");
                Require(Mathf.Abs(Mathf.DeltaAngle(instance.localEulerAngles.z, -17.0f)) < 0.0001f, "unity-object-rotation-mapping");
                Require(instance.localScale.x < -1.19f && instance.localScale.x > -1.21f, "unity-object-flip-scale");
                Transform visual = instance.Find("Visual");
                Require(visual != null, "unity-pivot-visual-child");
                Require(Mathf.Abs(visual.localPosition.x) > 0.0001f, "unity-pivot-offset-x");
                SpriteRenderer renderer = visual.GetComponent<SpriteRenderer>();
                Require(renderer != null && renderer.sprite != null, "unity-sprite-materialization");

                RenderTexture target = new RenderTexture(640, 360, 24, RenderTextureFormat.ARGB32);
                camera.targetTexture = target;
                camera.Render();
                RenderTexture.active = target;
                Texture2D capture = new Texture2D(target.width, target.height, TextureFormat.RGBA32, false);
                capture.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0);
                capture.Apply();
                Color32[] pixels = capture.GetPixels32();
                int visiblePixels = 0;
                foreach (Color32 pixel in pixels)
                {
                    if (pixel.a > 8)
                        visiblePixels++;
                }
                Require(visiblePixels > 0, "unity-render-no-visible-pixels");
                string output = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "unity-professional-capture.png");
                File.WriteAllBytes(output, capture.EncodeToPNG());
                File.WriteAllText(
                    Path.Combine(Directory.GetParent(Application.dataPath).FullName, "unity-professional-validation-result.txt"),
                    "P2D04_UNITY_VALIDATION=SUCCESS\n" +
                    "P2D04_UNITY_RENDER_PIXELS=" + visiblePixels + "\n" +
                    "P2D04_UNITY_VERSION=" + Application.unityVersion + "\n");
                camera.targetTexture = null;
                RenderTexture.active = null;
                UnityEngine.Object.DestroyImmediate(capture);
                UnityEngine.Object.DestroyImmediate(target);
                UnityEngine.Object.DestroyImmediate(root);
                AssetDatabase.SaveAssets();
                Debug.Log("P2D04_UNITY_VALIDATION=SUCCESS");
                Debug.Log("P2D04_UNITY_RENDER_PIXELS=" + visiblePixels);
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                string result = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "unity-professional-validation-result.txt");
                File.WriteAllText(result, "P2D04_UNITY_VALIDATION=FAILED\nREASON=" + exception.Message + "\n");
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }
    }
}
