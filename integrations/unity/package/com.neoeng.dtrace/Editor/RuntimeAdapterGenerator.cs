using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class RuntimeAdapterGenerator
    {
        private const string DefaultBundlePath = "Assets/NeoEngGenerated/runtime-adapters.json";
        private static readonly string[] Capabilities =
        {
            "runtime.scene_loading", "runtime.lifecycle", "runtime.fixed_update",
            "runtime.lighting", "runtime.shaders", "runtime.particles",
            "runtime.post_processing", "runtime.triggers", "runtime.streaming",
        };

        public static GameObject Import(string bundlePath)
        {
            string normalized = NormalizeAssetPath(bundlePath);
            string absolute = Path.Combine(Directory.GetCurrentDirectory(), normalized);
            if (!File.Exists(absolute)) throw new InvalidDataException("runtime adapter bundle does not exist");
            byte[] bundleBytes = File.ReadAllBytes(absolute);
            AdapterBundle bundle = JsonUtility.FromJson<AdapterBundle>(System.Text.Encoding.UTF8.GetString(bundleBytes));
            Validate(bundle, absolute, bundleBytes);

            GameObject root = new GameObject("NeoEngRuntimeScene");
            NeoEngRuntimeAdapterMetadata metadata = root.AddComponent<NeoEngRuntimeAdapterMetadata>();
            metadata.adapterEngine = "unity";
            metadata.bundleSha256 = FileSha256(absolute);
            metadata.scenarioSha256 = bundle.source.sha256;
            metadata.fixedTick = 0;
            metadata.simulationTime = 0.0;
            metadata.serializedCapabilities = JsonUtility.ToJson(bundle.capabilities.unity.support);

            string baseDirectory = Path.GetDirectoryName(absolute);
            string scenarioPath = SafeCombine(Directory.GetCurrentDirectory(), bundle.source.path);
            ScenarioExport scenario = JsonUtility.FromJson<ScenarioExport>(File.ReadAllText(scenarioPath));
            for (int index = 0; index < scenario.layers.Length; index++)
            {
                ScenarioLayerData source = scenario.layers[index];
                GameObject layer = new GameObject("Layer_" + index);
                layer.transform.SetParent(root.transform, false);
                layer.SetActive(source.visible);
                NeoEngScenarioLayerMetadata layerMetadata = layer.AddComponent<NeoEngScenarioLayerMetadata>();
                layerMetadata.layerId = source.id;
                layerMetadata.layerName = source.name;
                layerMetadata.visible = source.visible;
                layerMetadata.objectIds = source.object_ids ?? Array.Empty<string>();
                layerMetadata.parallaxDepth = source.parallax.depth;
                layerMetadata.parallaxTranslationStrength = source.parallax.translation_strength;
                layerMetadata.parallaxZoomStrength = source.parallax.zoom_strength;
            }
            foreach (SidecarData sidecar in bundle.sidecars)
            {
                GameObject sidecarObject = new GameObject("Sidecar_" + sidecar.capability);
                sidecarObject.transform.SetParent(root.transform, false);
                NeoEngRuntimeSidecarMetadata sidecarMetadata = sidecarObject.AddComponent<NeoEngRuntimeSidecarMetadata>();
                sidecarMetadata.capability = sidecar.capability;
                sidecarMetadata.formatId = sidecar.format_id;
                sidecarMetadata.schemaVersion = sidecar.schema_version;
                sidecarMetadata.sha256 = sidecar.sha256;
                sidecarMetadata.bytes = sidecar.bytes;
                SupportData decision = bundle.capabilities.unity.support.First(item => item.id == sidecar.capability);
                sidecarMetadata.compatibility = decision.compatibility;
                sidecarMetadata.mode = decision.mode;
                sidecarMetadata.reason = decision.reason;
            }
            return root;
        }

        public static void RunHeadlessRuntimeAdapter()
        {
            try
            {
                string path = Environment.GetEnvironmentVariable("NEOENG_RUNTIME_ADAPTER_BUNDLE");
                GameObject root = Import(string.IsNullOrWhiteSpace(path) ? DefaultBundlePath : path);
                NeoEngRuntimeAdapterMetadata metadata = root.GetComponent<NeoEngRuntimeAdapterMetadata>();
                metadata.fixedTick = 3;
                metadata.simulationTime = 3.0 / 60.0;
                Debug.Log("RUNTIME_ADAPTER_UNITY=SUCCESS");
                Debug.Log("RUNTIME_ADAPTER_LAYERS=" + root.transform.Cast<Transform>().Count(item => item.name.StartsWith("Layer_", StringComparison.Ordinal)));
                Debug.Log("RUNTIME_ADAPTER_SIDECARS=" + root.transform.Cast<Transform>().Count(item => item.name.StartsWith("Sidecar_", StringComparison.Ordinal)));
                Debug.Log("RUNTIME_ADAPTER_FIXED_TICK=" + metadata.fixedTick);
                UnityEngine.Object.DestroyImmediate(root);
                AssetDatabase.SaveAssets();
                EditorApplication.Exit(0);
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }

        private static string NormalizeAssetPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) throw new InvalidDataException("runtime adapter bundle path is empty");
            string normalized = path.Replace('\\', '/');
            if (normalized.StartsWith("/", StringComparison.Ordinal) || normalized.Contains("..", StringComparison.Ordinal) || Path.IsPathRooted(normalized))
                throw new InvalidDataException("runtime adapter bundle path is unsafe");
            return normalized;
        }

        private static string SafeCombine(string root, string relative)
        {
            if (string.IsNullOrWhiteSpace(relative) || relative.Contains("..", StringComparison.Ordinal) || relative.Contains('\\') || Path.IsPathRooted(relative))
                throw new InvalidDataException("runtime adapter reference path is unsafe");
            string candidate = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            string rootFull = Path.GetFullPath(root) + Path.DirectorySeparatorChar;
            if (!candidate.StartsWith(rootFull, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("runtime adapter reference escapes root");
            return candidate;
        }

        private static void Validate(AdapterBundle bundle, string bundlePath, byte[] bundleBytes)
        {
            if (bundle == null || bundle.format_id != "neoeng-d-trace-runtime-adapters" || bundle.schema_version != 1 || bundle.api_version != 1)
                throw new InvalidDataException("unsupported runtime adapter bundle");
            if (bundle.generator == null || bundle.generator.id != "neoeng_d_trace") throw new InvalidDataException("runtime adapter generator is invalid");
            ValidateFile(bundle.source.path, bundle.source.sha256, bundle.source.bytes, Directory.GetCurrentDirectory(), "scenario source");
            if (bundle.sidecars == null || bundle.sidecars.Length != 6) throw new InvalidDataException("runtime adapter sidecars are incomplete");
            HashSet<string> seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (SidecarData sidecar in bundle.sidecars)
            {
                if (sidecar == null || !seen.Add(sidecar.capability) || !Capabilities.Contains(sidecar.capability, StringComparer.Ordinal)) throw new InvalidDataException("runtime adapter sidecar capability is invalid");
                ValidateFile(sidecar.path, sidecar.sha256, sidecar.bytes, Directory.GetCurrentDirectory(), sidecar.capability);
                if (!sidecar.required) throw new InvalidDataException("runtime adapter sidecars must be required");
            }
            if (seen.Count != 6 || bundle.capabilities == null || bundle.capabilities.unity == null || bundle.capabilities.unity.support == null || bundle.capabilities.unity.support.Length != Capabilities.Length)
                throw new InvalidDataException("runtime adapter capability matrix is incomplete");
            if (bundle.capabilities.unity.support.Select(item => item.id).Distinct(StringComparer.Ordinal).Count() != Capabilities.Length)
                throw new InvalidDataException("runtime adapter capability matrix has duplicates");
        }

        private static void ValidateFile(string relative, string expectedHash, int expectedBytes, string root, string label)
        {
            string path = SafeCombine(root, relative);
            if (!File.Exists(path) || FileSha256(path) != expectedHash || new FileInfo(path).Length != expectedBytes)
                throw new InvalidDataException(label + " hash or size mismatch");
        }

        private static string FileSha256(string path)
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = File.OpenRead(path))
                return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }

        [Serializable] private sealed class AdapterBundle { public string format_id; public int schema_version; public int api_version; public GeneratorData generator; public FileBinding source; public SidecarData[] sidecars; public CapabilityData capabilities; }
        [Serializable] private sealed class GeneratorData { public string id; public string version; }
        [Serializable] private class FileBinding { public string path; public string format_id; public int schema_version; public string sha256; public int bytes; }
        [Serializable] private sealed class SidecarData { public string capability; public string path; public string format_id; public int schema_version; public string sha256; public int bytes; public bool required; }
        [Serializable] private sealed class CapabilityData { public EngineData godot; public EngineData unity; }
        [Serializable] private sealed class EngineData { public string adapter_id; public int adapter_version; public SupportData[] support; }
        [Serializable] private sealed class SupportData { public string id; public string compatibility; public string mode; public string reason; }
        [Serializable] private sealed class ScenarioExport { public ScenarioLayerData[] layers; }
        [Serializable] private sealed class ScenarioLayerData { public string id; public string name; public bool visible; public string[] object_ids; public ParallaxData parallax; }
        [Serializable] private sealed class ParallaxData { public float depth; public float translation_strength; public float zoom_strength; }
    }
}
