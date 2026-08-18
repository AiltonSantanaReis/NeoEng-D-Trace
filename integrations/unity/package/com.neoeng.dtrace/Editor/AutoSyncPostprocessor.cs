using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace NeoEng.DTrace.Editor
{
    /// <summary>
    /// Engine-native automatic synchronization entry point.
    /// It consumes Unity's asset import event and delegates all validation,
    /// conflict protection and atomic per-manifest import behavior to the generator.
    /// </summary>
    public sealed class AutoSyncPostprocessor : AssetPostprocessor
    {
        private static readonly HashSet<string> PendingChanges = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private static bool scheduled;
        private static bool running;
        private static readonly Dictionary<string, int> HashRetryCounts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

        private static void OnPostprocessAllAssets(
            string[] importedAssets,
            string[] deletedAssets,
            string[] movedAssets,
            string[] movedFromAssetPaths)
        {
            QueueChanges(importedAssets);
            QueueChanges(deletedAssets);
            QueueChanges(movedAssets);
            QueueChanges(movedFromAssetPaths);
            if (PendingChanges.Count == 0 || scheduled || running)
            {
                return;
            }
            scheduled = true;
            EditorApplication.delayCall += RunScheduled;
        }

        private static void QueueChanges(IEnumerable<string> paths)
        {
            foreach (string path in paths ?? Array.Empty<string>())
            {
                if (!string.IsNullOrWhiteSpace(path))
                {
                    PendingChanges.Add(path);
                }
            }
        }

        private static void RunScheduled()
        {
            scheduled = false;
            string[] changes = PendingChanges.ToArray();
            PendingChanges.Clear();
            ProcessChangedAssets(changes);
        }

        /// <summary>
        /// Shared production path used by the Unity event callback and real editor validation.
        /// </summary>
        public static void ProcessChangedAssets(IEnumerable<string> changedAssetPaths)
        {
            if (running)
            {
                return;
            }
            string[] manifests = UnityImportGenerator.FindManifestsAffectedByAssets(changedAssetPaths);
            if (manifests.Length == 0)
            {
                return;
            }

            running = true;
            try
            {
                UnityImportGenerator.ImportBatchResult batch =
                    UnityImportGenerator.ImportManifests(manifests);
                if (!batch.Success)
                {
                    Debug.LogError("UNITY_NATIVE_AUTO_SYNC=GLOBAL_ROLLBACK error=" + batch.ErrorSummary());
                    foreach (string manifest in manifests)
                    {
                        ScheduleHashRetry(manifest, batch.Error);
                    }
                    return;
                }
                foreach (UnityImportGenerator.ImportResult result in batch.Results)
                {
                    string status = result.UpdatedAssets > 0 ? "UPDATED" : "UNCHANGED";
                    Debug.Log("UNITY_NATIVE_AUTO_SYNC=" + status + " transaction=GLOBAL");
                }
            }
            finally
            {
                running = false;
            }
        }
        private static void ScheduleHashRetry(string manifest, string error)
        {
            if (error == null || error.IndexOf("hash", StringComparison.OrdinalIgnoreCase) < 0)
            {
                return;
            }
            int count = HashRetryCounts.TryGetValue(manifest, out int previous) ? previous : 0;
            if (count >= 1)
            {
                return;
            }
            HashRetryCounts[manifest] = count + 1;
            Debug.Log("UNITY_NATIVE_AUTO_SYNC=RETRY manifest=" + manifest + " reason=hash_mismatch");
            EditorApplication.delayCall += () => ProcessChangedAssets(new[] { manifest });
        }
    }
}