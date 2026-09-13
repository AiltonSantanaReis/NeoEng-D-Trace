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
    /// Materializes the bounded hybrid 3D vertical slice with native Unity
    /// objects. All source bindings are checked before any scene object is
    /// created, so a changed package fails closed.
    /// </summary>
    public static class NeoEngRuntimeHybrid3D
    {
        private const string FormatId = "neoeng-d-trace-hybrid-runtime";
        private const int SchemaVersion = 1;
        private const string SceneFormatId = "neoeng-d-trace-hybrid-runtime-scene";
        private const int SceneSchemaVersion = 1;

        [Serializable]
        public sealed class FileBinding
        {
            public string path;
            public string sha256;
            public long bytes;
            public bool required;
        }

        [Serializable]
        public sealed class SceneBindings
        {
            public FileBinding authoring;
            public FileBinding normalized;
        }

        [Serializable]
        public sealed class AnimationBindings
        {
            public FileBinding manifest;
            public FileBinding first_frame;
            public int frame_count;
        }

        [Serializable]
        public sealed class RuntimeManifest
        {
            public string format_id;
            public int schema_version;
            public string support_status;
            public SceneBindings scene;
            public AnimationBindings animation;
        }

        [Serializable]
        public sealed class PointData
        {
            public float x;
            public float y;
            public float z;
        }

        [Serializable]
        public sealed class CameraData
        {
            public string projection;
            public float fov_degrees;
            public float near;
            public float far;
            public PointData position;
            public PointData target;
        }

        [Serializable]
        public sealed class MaterialData
        {
            public string id;
            public float metallic;
            public float roughness;
            public float[] base_color;
        }

        [Serializable]
        public sealed class TriangleData
        {
            public int a;
            public int b;
            public int c;
        }

        [Serializable]
        public sealed class MeshData
        {
            public string id;
            public string material_id;
            public PointData position;
            public PointData[] vertices;
            public TriangleData[] triangles;
        }

        [Serializable]
        public sealed class LightData
        {
            public string id;
            public string type;
            public float intensity;
            public PointData position;
        }

        [Serializable]
        public sealed class KeyframeData
        {
            public float time;
            public PointData position;
        }

        [Serializable]
        public sealed class ClipData
        {
            public string id;
            public string mesh_id;
            public KeyframeData[] keyframes;
        }

        [Serializable]
        public sealed class RuntimeScene
        {
            public string format_id;
            public int schema_version;
            public string support_status;
            public CameraData camera;
            public MaterialData[] materials;
            public MeshData[] meshes;
            public LightData[] lights;
            public ClipData[] animation_clips;
        }

        [Serializable]
        private sealed class AnimationFrame
        {
            public string texture;
        }

        [Serializable]
        private sealed class AnimationManifest
        {
            public string format_id;
            public int schema_version;
            public int frame_count;
            public AnimationFrame[] frames;
        }

        public sealed class Result
        {
            public GameObject Root { get; internal set; }
            public Camera Camera { get; internal set; }
            public GameObject AnimatedObject { get; internal set; }
            public RuntimeManifest Manifest { get; internal set; }
            public RuntimeScene Scene { get; internal set; }
            public int MeshCount { get; internal set; }
            public int MaterialCount { get; internal set; }
            public int LightCount { get; internal set; }
            public int AnimationClipCount { get; internal set; }
            public int AnimationFrameCount { get; internal set; }
            public bool AnimationFrameLoaded { get; internal set; }
            public float PlaybackPositionY { get; internal set; }
        }

        public static Result Import(string runtimeManifestPath)
        {
            if (string.IsNullOrWhiteSpace(runtimeManifestPath))
                throw new InvalidDataException("hybrid runtime manifest path is empty");
            string fullManifestPath = Path.GetFullPath(runtimeManifestPath);
            if (!File.Exists(fullManifestPath))
                throw new FileNotFoundException("hybrid runtime manifest was not found", fullManifestPath);
            string baseDirectory = Path.GetDirectoryName(fullManifestPath);
            RuntimeManifest manifest = JsonUtility.FromJson<RuntimeManifest>(File.ReadAllText(fullManifestPath, Encoding.UTF8));
            ValidateManifest(manifest, baseDirectory);
            string normalizedPath = ResolveBinding(baseDirectory, manifest.scene.normalized, "scene.normalized");
            RuntimeScene scene = JsonUtility.FromJson<RuntimeScene>(File.ReadAllText(normalizedPath, Encoding.UTF8));
            ValidateScene(scene);
            string animationPath = ResolveBinding(baseDirectory, manifest.animation.manifest, "animation.manifest");
            AnimationManifest animationManifest = JsonUtility.FromJson<AnimationManifest>(File.ReadAllText(animationPath, Encoding.UTF8));
            if (animationManifest == null || animationManifest.frames == null || animationManifest.frames.Length == 0
                || animationManifest.frame_count != manifest.animation.frame_count)
                throw new InvalidDataException("hybrid animation manifest is invalid");
            string firstFramePath = ResolveBinding(baseDirectory, manifest.animation.first_frame, "animation.first_frame");
            byte[] firstFrameBytes = File.ReadAllBytes(firstFramePath);
            Texture2D firstFrame = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            if (!firstFrame.LoadImage(firstFrameBytes, false))
                throw new InvalidDataException("hybrid animation first frame could not be decoded by Unity");

            GameObject root = new GameObject("NeoEngRuntimeHybrid3D");
            root.SetActive(false);
            GameObject cameraObject = new GameObject("PerspectiveCamera");
            cameraObject.transform.SetParent(root.transform, false);
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = false;
            camera.fieldOfView = scene.camera.fov_degrees;
            camera.nearClipPlane = scene.camera.near;
            camera.farClipPlane = scene.camera.far;
            camera.transform.position = Point(scene.camera.position);
            camera.transform.LookAt(Point(scene.camera.target));

            Dictionary<string, Material> materials = new Dictionary<string, Material>(StringComparer.Ordinal);
            foreach (MaterialData source in scene.materials)
            {
                Shader shader = Shader.Find("Standard") ?? Shader.Find("Unlit/Color");
                if (shader == null)
                    throw new InvalidDataException("Unity could not resolve a 3D material shader");
                Material material = new Material(shader) { name = source.id };
                material.SetFloat("_Metallic", source.metallic);
                material.SetFloat("_Glossiness", 1.0f - Mathf.Clamp01(source.roughness));
                if (source.base_color != null && source.base_color.Length >= 4)
                    material.color = new Color(source.base_color[0], source.base_color[1], source.base_color[2], source.base_color[3]);
                materials.Add(source.id, material);
            }

            Dictionary<string, GameObject> meshes = new Dictionary<string, GameObject>(StringComparer.Ordinal);
            foreach (MeshData source in scene.meshes)
            {
                GameObject meshObject = new GameObject(source.id);
                meshObject.transform.SetParent(root.transform, false);
                meshObject.transform.localPosition = Point(source.position);
                Mesh mesh = new Mesh { name = source.id + "Mesh" };
                mesh.vertices = source.vertices.Select(Point).ToArray();
                mesh.triangles = source.triangles.SelectMany(triangle => new[] { triangle.a, triangle.b, triangle.c }).ToArray();
                mesh.RecalculateNormals();
                meshObject.AddComponent<MeshFilter>().sharedMesh = mesh;
                MeshRenderer renderer = meshObject.AddComponent<MeshRenderer>();
                renderer.sharedMaterial = materials[source.material_id];
                meshes.Add(source.id, meshObject);
            }

            foreach (LightData source in scene.lights)
            {
                GameObject lightObject = new GameObject(source.id);
                lightObject.transform.SetParent(root.transform, false);
                lightObject.transform.position = Point(source.position);
                Light light = lightObject.AddComponent<Light>();
                light.type = source.type == "point" ? LightType.Point : LightType.Directional;
                light.intensity = source.intensity;
                if (light.type == LightType.Directional)
                    lightObject.transform.LookAt(Vector3.zero);
            }

            ClipData firstClip = scene.animation_clips[0];
            GameObject animated = meshes[firstClip.mesh_id];
            AnimationClip clip = new AnimationClip { name = firstClip.id, legacy = true, wrapMode = WrapMode.Loop };
            Keyframe[] keys = firstClip.keyframes.Select(keyframe => new Keyframe(keyframe.time, keyframe.position.y)).ToArray();
            clip.SetCurve(string.Empty, typeof(Transform), "localPosition.y", new AnimationCurve(keys));
            Animation animation = animated.AddComponent<Animation>();
            animation.AddClip(clip, clip.name);
            root.SetActive(true);
            animation.Play(clip.name);
            AnimationState state = animation[clip.name];
            state.time = firstClip.keyframes[firstClip.keyframes.Length - 1].time * 0.5f;
            animation.Sample();
            if (float.IsNaN(animated.transform.localPosition.y) || float.IsInfinity(animated.transform.localPosition.y))
                throw new InvalidDataException("hybrid animation playback produced a non-finite position");

            return new Result
            {
                Root = root,
                Camera = camera,
                AnimatedObject = animated,
                Manifest = manifest,
                Scene = scene,
                MeshCount = scene.meshes.Length,
                MaterialCount = scene.materials.Length,
                LightCount = scene.lights.Length,
                AnimationClipCount = scene.animation_clips.Length,
                AnimationFrameCount = manifest.animation.frame_count,
                AnimationFrameLoaded = firstFrame != null,
                PlaybackPositionY = animated.transform.localPosition.y,
            };
        }

        private static void ValidateManifest(RuntimeManifest manifest, string baseDirectory)
        {
            if (manifest == null || manifest.format_id != FormatId || manifest.schema_version != SchemaVersion
                || manifest.support_status != "VERTICAL_SLICE_ONLY" || manifest.scene == null || manifest.animation == null)
                throw new InvalidDataException("unsupported hybrid runtime manifest");
            ResolveBinding(baseDirectory, manifest.scene.authoring, "scene.authoring");
            ResolveBinding(baseDirectory, manifest.scene.normalized, "scene.normalized");
            ResolveBinding(baseDirectory, manifest.animation.manifest, "animation.manifest");
            ResolveBinding(baseDirectory, manifest.animation.first_frame, "animation.first_frame");
            if (manifest.animation.frame_count <= 0)
                throw new InvalidDataException("hybrid runtime animation frame count is invalid");
        }

        private static void ValidateScene(RuntimeScene scene)
        {
            if (scene == null || scene.format_id != SceneFormatId || scene.schema_version != SceneSchemaVersion
                || scene.support_status != "VERTICAL_SLICE_ONLY" || scene.camera == null
                || scene.camera.projection != "perspective" || scene.materials == null || scene.materials.Length == 0
                || scene.meshes == null || scene.meshes.Length == 0 || scene.lights == null || scene.lights.Length == 0
                || scene.animation_clips == null || scene.animation_clips.Length == 0)
                throw new InvalidDataException("unsupported hybrid runtime scene");
            HashSet<string> materialIds = new HashSet<string>(scene.materials.Select(item => item.id), StringComparer.Ordinal);
            if (materialIds.Count != scene.materials.Length || materialIds.Contains(string.Empty))
                throw new InvalidDataException("hybrid runtime material IDs are invalid");
            HashSet<string> meshIds = new HashSet<string>(StringComparer.Ordinal);
            foreach (MeshData mesh in scene.meshes)
            {
                if (mesh == null || string.IsNullOrWhiteSpace(mesh.id) || !meshIds.Add(mesh.id)
                    || !materialIds.Contains(mesh.material_id) || mesh.vertices == null || mesh.vertices.Length < 3
                    || mesh.triangles == null || mesh.triangles.Length == 0)
                    throw new InvalidDataException("hybrid runtime mesh data is invalid");
                foreach (TriangleData triangle in mesh.triangles)
                    if (triangle == null || triangle.a < 0 || triangle.b < 0 || triangle.c < 0
                        || triangle.a >= mesh.vertices.Length || triangle.b >= mesh.vertices.Length || triangle.c >= mesh.vertices.Length)
                        throw new InvalidDataException("hybrid runtime triangle indices are invalid");
            }
            foreach (LightData light in scene.lights)
                if (light == null || (light.type != "directional" && light.type != "point") || light.intensity < 0.0f)
                    throw new InvalidDataException("hybrid runtime light data is invalid");
            foreach (ClipData clip in scene.animation_clips)
                if (clip == null || !meshIds.Contains(clip.mesh_id) || clip.keyframes == null || clip.keyframes.Length < 2)
                    throw new InvalidDataException("hybrid runtime animation data is invalid");
        }

        private static string ResolveBinding(string baseDirectory, FileBinding binding, string label)
        {
            if (binding == null || string.IsNullOrWhiteSpace(binding.path) || binding.path.Contains("\\")
                || binding.path.Contains(":") || Path.IsPathRooted(binding.path))
                throw new InvalidDataException(label + " must be a safe relative path");
            string[] parts = binding.path.Split('/');
            if (parts.Any(part => string.IsNullOrEmpty(part) || part == "." || part == ".."))
                throw new InvalidDataException(label + " must be a safe relative path");
            string root = Path.GetFullPath(baseDirectory).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string fullPath = Path.GetFullPath(Path.Combine(root, binding.path.Replace('/', Path.DirectorySeparatorChar)));
            if (!fullPath.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) || !File.Exists(fullPath))
                throw new InvalidDataException(label + " file does not exist or escapes the package");
            byte[] bytes = File.ReadAllBytes(fullPath);
            if (binding.bytes != bytes.LongLength || !string.Equals(binding.sha256, Sha256(bytes), StringComparison.Ordinal))
                throw new InvalidDataException(label + " file hash mismatch or size mismatch");
            return fullPath;
        }

        private static Vector3 Point(PointData value)
        {
            if (value == null)
                throw new InvalidDataException("hybrid runtime point is missing");
            return new Vector3(value.x, value.y, value.z);
        }

        private static string Sha256(byte[] bytes)
        {
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", string.Empty).ToLowerInvariant();
        }
    }
}
