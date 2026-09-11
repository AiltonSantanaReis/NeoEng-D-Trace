using System;
using System.Collections.Generic;
using System.IO;
using System.Globalization;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace NeoEng.DTrace
{
    /// <summary>
    /// Deterministic runtime consumer for the v1 particle sidecar.
    /// The component feeds the validated state into Unity's native
    /// ParticleSystem renderer instead of letting the engine emit a second,
    /// unrelated simulation.
    /// </summary>
    public sealed class NeoEngRuntimeParticles : MonoBehaviour
    {
        private const uint Uint32Mask = 0xffffffffu;
        private const double Uint32Scale = 1.0 / 4294967296.0;
        private const int MaxEmitters = 1024;
        private const int MaxParticlesPerEmitter = 100000;
        private const int MaxTotalParticles = 200000;

        [Serializable]
        public sealed class Point3Data
        {
            public float x;
            public float y;
            public float z;
        }

        [Serializable]
        public sealed class SourceData
        {
            public string format_id;
            public int schema_version;
            public string sha256;
        }

        [Serializable]
        public sealed class EmitterData
        {
            public Point3Data acceleration;
            public int burst_count;
            public float emission_rate;
            public bool enabled;
            public string id;
            public Point3Data initial_velocity;
            public float lifetime;
            public int max_particles;
            public Point3Data origin;
            public long seed;
            public Point3Data velocity_spread;
        }

        [Serializable]
        public sealed class ParticleDocumentData
        {
            public string format_id;
            public int schema_version;
            public int algorithm_version;
            public SourceData source;
            public float fixed_dt;
            public int max_substeps;
            public EmitterData[] emitters;
        }

        private sealed class ParticleState
        {
            public int particleId;
            public double age;
            public readonly double[] position = new double[3];
            public readonly double[] velocity = new double[3];
        }

        private sealed class EmitterState
        {
            public uint rngState;
            public double emissionRemainder;
            public int burstPending;
            public int nextParticleId;
            public readonly List<ParticleState> particles = new List<ParticleState>();
        }

        private sealed class EmitterRuntime
        {
            public EmitterData data;
            public EmitterState state;
            public ParticleSystem renderer;
            public ParticleSystem.Particle[] buffer;
        }

        private ParticleDocumentData _document;
        private readonly List<EmitterRuntime> _emitters = new List<EmitterRuntime>();
        private double _accumulator;

        public bool autoAdvance = true;
        public int ParticleCount { get; private set; }
        public int EmitterCount { get { return _emitters.Count; } }
        public int TickIndex { get; private set; }
        public double SimulationTime { get; private set; }
        public string StateSha256 { get; private set; } = string.Empty;
        public string LastError { get; private set; } = string.Empty;

        private void Update()
        {
            if (!autoAdvance || _document == null || _document.fixed_dt <= 0.0)
                return;
            _accumulator += Math.Max(0.0, Time.deltaTime);
            int steps = Math.Min(
                _document.max_substeps,
                (int)Math.Floor(_accumulator / _document.fixed_dt + 1e-12));
            for (int index = 0; index < steps; index++)
                Step(_document.fixed_dt);
            _accumulator -= steps * _document.fixed_dt;
            if (steps > 0)
            {
                TickIndex += steps;
                SimulationTime += steps * _document.fixed_dt;
                ApplyNativeRenderers();
            }
        }

        public bool ConfigureFromJson(string json, out string error)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(json))
                    throw new InvalidDataException("particle sidecar is empty");
                ParticleDocumentData candidate = JsonUtility.FromJson<ParticleDocumentData>(json);
                Validate(candidate);
                Configure(candidate);
                error = string.Empty;
                return true;
            }
            catch (Exception exception)
            {
                LastError = exception.Message;
                error = LastError;
                return false;
            }
        }

        public bool AdvanceFixedTicks(int ticks)
        {
            if (_document == null || ticks < 0 || ticks > 100000)
                return false;
            for (int index = 0; index < ticks; index++)
                Step(_document.fixed_dt);
            TickIndex += ticks;
            SimulationTime += ticks * _document.fixed_dt;
            ApplyNativeRenderers();
            return true;
        }

        public bool ResetSimulation()
        {
            if (_document == null)
                return false;
            Configure(_document);
            return true;
        }

        private void Configure(ParticleDocumentData document)
        {
            _document = document;
            _emitters.Clear();
            _accumulator = 0.0;
            TickIndex = 0;
            SimulationTime = 0.0;
            LastError = string.Empty;
            foreach (EmitterData emitter in document.emitters.OrderBy(item => item.id, StringComparer.Ordinal))
            {
                GameObject child = new GameObject("ParticleEmitter_" + emitter.id);
                child.transform.SetParent(transform, false);
                ParticleSystem particleSystem = child.AddComponent<ParticleSystem>();
                ParticleSystem.MainModule main = particleSystem.main;
                main.loop = false;
                main.playOnAwake = false;
                main.maxParticles = emitter.max_particles;
                main.startLifetime = (float)emitter.lifetime;
                main.simulationSpace = ParticleSystemSimulationSpace.Local;
                ParticleSystem.EmissionModule emission = particleSystem.emission;
                emission.enabled = false;
                ParticleSystemRenderer renderer = child.GetComponent<ParticleSystemRenderer>();
                renderer.renderMode = ParticleSystemRenderMode.Billboard;
                particleSystem.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                _emitters.Add(new EmitterRuntime
                {
                    data = emitter,
                    state = new EmitterState
                    {
                        rngState = unchecked((uint)emitter.seed),
                        burstPending = emitter.burst_count,
                    },
                    renderer = particleSystem,
                    buffer = new ParticleSystem.Particle[emitter.max_particles],
                });
            }
            ApplyNativeRenderers();
        }

        private void Step(double dt)
        {
            foreach (EmitterRuntime emitter in _emitters)
            {
                EmitterData data = emitter.data;
                EmitterState state = emitter.state;
                if (data.enabled)
                {
                    int available = data.max_particles - state.particles.Count;
                    int burst = Math.Min(state.burstPending, Math.Max(0, available));
                    state.burstPending -= burst;
                    state.emissionRemainder += data.emission_rate * dt;
                    int continuous = Math.Min(
                        (int)Math.Floor(state.emissionRemainder),
                        Math.Max(0, available - burst));
                    state.emissionRemainder -= continuous;
                    for (int index = 0; index < burst + continuous; index++)
                        Spawn(data, state);
                }

                List<ParticleState> survivors = new List<ParticleState>(state.particles.Count);
                foreach (ParticleState particle in state.particles)
                {
                    particle.velocity[0] += Acceleration(data, 0) * dt;
                    particle.velocity[1] += Acceleration(data, 1) * dt;
                    particle.velocity[2] += Acceleration(data, 2) * dt;
                    particle.position[0] += particle.velocity[0] * dt;
                    particle.position[1] += particle.velocity[1] * dt;
                    particle.position[2] += particle.velocity[2] * dt;
                    particle.age += dt;
                    if (particle.age < data.lifetime)
                        survivors.Add(particle);
                }
                state.particles.Clear();
                state.particles.AddRange(survivors);
            }
        }

        private static double Acceleration(EmitterData data, int axis)
        {
            if (axis == 0) return data.acceleration.x;
            if (axis == 1) return data.acceleration.y;
            return data.acceleration.z;
        }

        private static void Spawn(EmitterData data, EmitterState state)
        {
            double randomX = NextRandom(ref state.rngState);
            double randomY = NextRandom(ref state.rngState);
            double randomZ = NextRandom(ref state.rngState);
            ParticleState particle = new ParticleState
            {
                particleId = state.nextParticleId++,
            };
            particle.position[0] = data.origin.x;
            particle.position[1] = data.origin.y;
            particle.position[2] = data.origin.z;
            particle.velocity[0] = data.initial_velocity.x + data.velocity_spread.x * (2.0 * randomX - 1.0);
            particle.velocity[1] = data.initial_velocity.y + data.velocity_spread.y * (2.0 * randomY - 1.0);
            particle.velocity[2] = data.initial_velocity.z + data.velocity_spread.z * (2.0 * randomZ - 1.0);
            state.particles.Add(particle);
        }

        private static double NextRandom(ref uint state)
        {
            unchecked
            {
                state = 1664525u * state + 1013904223u;
            }
            return state * Uint32Scale;
        }

        private void ApplyNativeRenderers()
        {
            ParticleCount = _emitters.Sum(item => item.state.particles.Count);
            foreach (EmitterRuntime emitter in _emitters)
            {
                int count = emitter.state.particles.Count;
                for (int index = 0; index < count; index++)
                {
                    ParticleState state = emitter.state.particles[index];
                    float life = Mathf.Max(0.0001f, (float)(emitter.data.lifetime - state.age));
                    ParticleSystem.Particle particle = new ParticleSystem.Particle
                    {
                        position = new Vector3(
                            (float)state.position[0],
                            (float)state.position[1],
                            (float)state.position[2]),
                        startColor = new Color(0.45f, 0.84f, 1.0f, Mathf.Clamp01(life / (float)emitter.data.lifetime)),
                        startSize = 0.18f + 0.08f * Mathf.Clamp01(life / (float)emitter.data.lifetime),
                        startLifetime = (float)emitter.data.lifetime,
                        remainingLifetime = life,
                    };
                    emitter.buffer[index] = particle;
                }
                emitter.renderer.SetParticles(emitter.buffer, count);
                emitter.renderer.Pause();
            }
            StateSha256 = ComputeStateSha256();
        }

        private string ComputeStateSha256()
        {
            StringBuilder builder = new StringBuilder();
            builder.Append(TickIndex.ToString(CultureInfo.InvariantCulture));
            foreach (EmitterRuntime emitter in _emitters)
            {
                builder.Append('|').Append(emitter.data.id);
                builder.Append('|').Append(emitter.state.rngState);
                builder.Append('|').Append(emitter.state.emissionRemainder.ToString("R", CultureInfo.InvariantCulture));
                foreach (ParticleState particle in emitter.state.particles.OrderBy(item => item.particleId))
                {
                    builder.Append('|').Append(particle.particleId);
                    builder.Append('|').Append(particle.age.ToString("R", CultureInfo.InvariantCulture));
                    for (int axis = 0; axis < 3; axis++)
                        builder.Append('|').Append(particle.position[axis].ToString("R", CultureInfo.InvariantCulture));
                    for (int axis = 0; axis < 3; axis++)
                        builder.Append('|').Append(particle.velocity[axis].ToString("R", CultureInfo.InvariantCulture));
                }
            }
            using (SHA256 sha = SHA256.Create())
            {
                return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(builder.ToString())))
                    .Replace("-", string.Empty)
                    .ToLowerInvariant();
            }
        }

        private static void Validate(ParticleDocumentData document)
        {
            if (document == null || document.format_id != "neoeng-d-trace-runtime-particles" || document.schema_version != 1 || document.algorithm_version != 1)
                throw new InvalidDataException("unsupported particle sidecar");
            if (document.source == null || document.source.format_id != "neoeng-d-trace-scenario-runtime" || document.source.schema_version != 1 || string.IsNullOrWhiteSpace(document.source.sha256))
                throw new InvalidDataException("particle source binding is invalid");
            if (!FinitePositive(document.fixed_dt) || document.max_substeps < 1 || document.max_substeps > 8)
                throw new InvalidDataException("particle fixed-step configuration is invalid");
            if (document.emitters == null || document.emitters.Length == 0 || document.emitters.Length > MaxEmitters)
                throw new InvalidDataException("particle emitters are invalid");
            HashSet<string> ids = new HashSet<string>(StringComparer.Ordinal);
            int total = 0;
            foreach (EmitterData emitter in document.emitters)
            {
                if (emitter == null || string.IsNullOrWhiteSpace(emitter.id) || !ids.Add(emitter.id))
                    throw new InvalidDataException("particle emitter IDs are invalid");
                if (emitter.seed < 0 || emitter.seed > Uint32Mask || !FiniteNonNegative(emitter.emission_rate) || !FinitePositive(emitter.lifetime))
                    throw new InvalidDataException("particle emitter values are invalid");
                if (emitter.max_particles < 1 || emitter.max_particles > MaxParticlesPerEmitter || emitter.burst_count < 0 || emitter.burst_count > emitter.max_particles)
                    throw new InvalidDataException("particle emitter capacity or burst is invalid");
                total += emitter.max_particles;
                if (total > MaxTotalParticles)
                    throw new InvalidDataException("particle document exceeds the capacity limit");
                ValidatePoint(emitter.initial_velocity, "initial_velocity");
                ValidatePoint(emitter.velocity_spread, "velocity_spread");
                ValidatePoint(emitter.acceleration, "acceleration");
                ValidatePoint(emitter.origin, "origin");
            }
        }

        private static void ValidatePoint(Point3Data point, string label)
        {
            if (point == null || !Finite(point.x) || !Finite(point.y) || !Finite(point.z))
                throw new InvalidDataException("particle " + label + " is invalid");
        }

        private static bool Finite(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }

        private static bool FinitePositive(double value)
        {
            return Finite(value) && value > 0.0;
        }

        private static bool FiniteNonNegative(double value)
        {
            return Finite(value) && value >= 0.0;
        }
    }
}
