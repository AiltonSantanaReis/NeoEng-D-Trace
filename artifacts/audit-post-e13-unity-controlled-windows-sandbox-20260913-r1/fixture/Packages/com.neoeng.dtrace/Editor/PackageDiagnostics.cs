using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.PackageManager;
using PackageInfo = UnityEditor.PackageManager.PackageInfo;
using UnityEngine;
using NeoEng.DTrace;

namespace NeoEng.DTrace.Editor
{
    public static class PackageDiagnostics
    {
        private static readonly string[] ForbiddenExtensions =
        {
            ".a", ".bundle", ".dll", ".dylib", ".exe", ".so"
        };

        [MenuItem("NeoEng D-Trace/Diagnostics/Validate UPM Package")]
        public static void RunFromMenu()
        {
            ValidationResult result = Validate();
            Debug.Log(result.ToJson());
            if (!result.Success)
            {
                throw new InvalidOperationException(result.ErrorSummary());
            }
        }

        public static void RunHeadless()
        {
            ValidationResult result = Validate();
            string output = Environment.GetEnvironmentVariable("NEOENG_STAGE5_REPORT");
            if (!string.IsNullOrWhiteSpace(output))
            {
                File.WriteAllText(output, result.ToJson() + "\n", new UTF8Encoding(false));
            }

            if (result.Success)
            {
                Debug.Log("UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS");
                Debug.Log("UNITY_PACKAGE_NAME=" + result.PackageName);
                Debug.Log("UNITY_PACKAGE_VERSION=" + result.PackageVersion);
                Debug.Log("UNITY_EDITOR_ASSEMBLY=LOADED");
                return;
            }

            Debug.LogError("UNITY_NATIVE_PACKAGE_STAGE5=FAILURE");
            Debug.LogError(result.ErrorSummary());
            EditorApplication.Exit(1);
        }

        public static ValidationResult Validate()
        {
            List<CheckResult> checks = new List<CheckResult>();
            PackageInfo package = PackageInfo.FindForAssembly(typeof(PackageDiagnostics).Assembly);
            if (package == null)
            {
                checks.Add(CheckResult.Fail("package_resolution", "PackageInfo was not resolved"));
                return ValidationResult.From(checks, null);
            }

            checks.Add(CheckResult.Equal("package_name", package.name, PackageIdentity.PackageName));
            checks.Add(CheckResult.Equal("package_version", package.version, PackageIdentity.PackageVersion));

            string packagePath = package.resolvedPath;
            if (string.IsNullOrWhiteSpace(packagePath) || !Directory.Exists(packagePath))
            {
                checks.Add(CheckResult.Fail("package_path", "resolved package path is unavailable"));
                return ValidationResult.From(checks, package);
            }

            string packageJson = Path.Combine(packagePath, "package.json");
            checks.Add(CheckResult.PassOrFail(
                "package_manifest",
                File.Exists(packageJson),
                "package.json exists"));
            checks.Add(CheckResult.PassOrFail(
                "runtime_assembly",
                File.Exists(Path.Combine(packagePath, "Runtime", "NeoEngDTrace.Runtime.asmdef")),
                "runtime asmdef exists"));
            checks.Add(CheckResult.PassOrFail(
                "editor_assembly",
                File.Exists(Path.Combine(packagePath, "Editor", "NeoEngDTrace.Editor.asmdef")),
                "editor asmdef exists"));
            checks.Add(CheckResult.PassOrFail(
                "identity_contract",
                PackageIdentity.IntegrationFormatId == "neoeng-d-trace-engine-integration" &&
                    PackageIdentity.IntegrationSchemaVersion == 1 &&
                    PackageIdentity.SourcePolicy == "source-only",
                "runtime identity contract is stable"));

            string[] forbidden = Directory.GetFiles(packagePath, "*", SearchOption.AllDirectories)
                .Where(path => ForbiddenExtensions.Contains(Path.GetExtension(path).ToLowerInvariant()))
                .Select(path => Path.GetFileName(path))
                .OrderBy(name => name, StringComparer.Ordinal)
                .ToArray();
            checks.Add(CheckResult.PassOrFail(
                "source_only",
                forbidden.Length == 0,
                forbidden.Length == 0 ? "no native or executable artifacts" : "forbidden: " + string.Join(",", forbidden)));

            return ValidationResult.From(checks, package);
        }

        [Serializable]
        public sealed class ValidationResult
        {
            public bool Success;
            public string PackageName;
            public string PackageVersion;
            public string SourcePolicy;
            public List<CheckResult> Checks;

            public static ValidationResult From(List<CheckResult> checks, PackageInfo package)
            {
                return new ValidationResult
                {
                    Success = checks.All(check => check.Success),
                    PackageName = package == null ? "" : package.name,
                    PackageVersion = package == null ? "" : package.version,
                    SourcePolicy = PackageIdentity.SourcePolicy,
                    Checks = checks
                };
            }

            public string ErrorSummary()
            {
                return string.Join("; ", Checks.Where(check => !check.Success).Select(check => check.Name + ": " + check.Detail));
            }

            public string ToJson()
            {
                return JsonUtility.ToJson(this, true);
            }
        }

        [Serializable]
        public sealed class CheckResult
        {
            public string Name;
            public bool Success;
            public string Detail;

            public static CheckResult PassOrFail(string name, bool success, string detail)
            {
                return new CheckResult { Name = name, Success = success, Detail = detail };
            }

            public static CheckResult Equal(string name, string actual, string expected)
            {
                return PassOrFail(name, actual == expected, "actual=" + actual + "; expected=" + expected);
            }

            public static CheckResult Pass(string name, string detail)
            {
                return PassOrFail(name, true, detail);
            }

            public static CheckResult Fail(string name, string detail)
            {
                return PassOrFail(name, false, detail);
            }
        }
    }
}
