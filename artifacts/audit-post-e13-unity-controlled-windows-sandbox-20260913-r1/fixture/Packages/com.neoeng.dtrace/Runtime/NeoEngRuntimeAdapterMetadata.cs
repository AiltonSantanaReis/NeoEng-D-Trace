using System;
using UnityEngine;

namespace NeoEng.DTrace
{
    [DisallowMultipleComponent]
    public sealed class NeoEngRuntimeAdapterMetadata : MonoBehaviour
    {
        public string adapterEngine;
        public string bundleSha256;
        public string scenarioSha256;
        public int fixedTick;
        public double simulationTime;
        public string serializedCapabilities;
    }

    [DisallowMultipleComponent]
    public sealed class NeoEngRuntimeSidecarMetadata : MonoBehaviour
    {
        public string capability;
        public string formatId;
        public int schemaVersion;
        public string sha256;
        public int bytes;
        public string compatibility;
        public string mode;
        public string reason;
    }
}
