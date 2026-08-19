namespace NeoEng.DTrace
{
    /// <summary>
    /// Stable source contract shared by the Unity package and the D-Trace manifest.
    /// </summary>
    public static class PackageIdentity
    {
        public const string PackageName = "com.neoeng.dtrace";
        public const string PackageVersion = "0.3.0";
        public const string IntegrationFormatId = "neoeng-d-trace-engine-integration";
        public const int IntegrationSchemaVersion = 1;
        public const string GeneratedRoot = "NeoEngGenerated";
        public const string OverrideSuffix = ".ndt.override.json";
        public const string SourcePolicy = "source-only";
    }
}
