# Registro de integridade — P2D-05/O-2-0

**Source commit:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Branch:** `p2d-05-quality-hardening`
**Status do relatório:** `PASS`
**Workloads:** `26/26`
**Erros:** `0`
**Frames determinísticos repetidos:** `26/26`

```text
Relatório: artifacts/p2d05/o2-0-baseline-20260830-restarted.json
Bytes: 145816
SHA-256: e88ab2b5db2b120424b800f03534354eba8d1a24639bf244778d14122e8e0d23

Produtor: scripts/benchmark_p2d_05_o2_preview.py
SHA-256: 9f6ff0eb1e2bea3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091
```

Os perfis CPU `o2-*.prof` permanecem apenas locais, pois podem conter
metadados de caminhos do ambiente. O relatório JSON é sanitizado e não contém
caminhos pessoais, segredos ou credenciais.
