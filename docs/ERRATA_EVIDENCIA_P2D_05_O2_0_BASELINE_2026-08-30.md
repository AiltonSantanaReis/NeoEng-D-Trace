# Errata — evidência P2D-05/O-2-0

**Documento corrigido:** `docs/EVIDENCIA_P2D_05_O2_0_BASELINE_2026-08-30.md`
**Data:** 30/08/2026 (UTC-03)

Na seção de normalização do produtor, a segunda linha do bloco de hashes foi
registrada com um espaço visual indevido no SHA-256. O valor canônico correto,
sem espaços, é:

```text
benchmark_p2d_05_o2_preview.py
9f6ff0eb1e2bea3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091

benchmark_p2d_05_o2_preview_reuse.py
9f6ff0eb1e2bea3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091
```

O comando efetivamente executado confirmou `EQUAL=True`. Esta errata substitui
somente a apresentação daquela linha; não altera o produtor, o relatório,
qualquer resultado de timing, o source commit ou a classificação O-2-0.
