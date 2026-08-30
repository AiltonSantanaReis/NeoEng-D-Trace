# Evidência P2D-04 — publicação posterior ao snapshot técnico

**Tipo:** adendo factual append-only
**Data:** 30/08/2026 (UTC-03)
**Finalidade:** registrar o ciclo remoto ocorrido depois do snapshot técnico de P2D-04
**Não é:** reescrita da evidência pós-commit original nem novo aceite funcional

## 1. Relação com o snapshot anterior

docs/EVIDENCIA_P2D_04_POSTCOMMIT_2026-08-30.md permanece imutável. Ele
registrava o estado no momento em que a qualificação técnica local foi
concluída e, naquele momento, informava corretamente que push e merge ainda
não haviam ocorrido.

Este adendo registra somente os eventos posteriores. Nenhum fato, hash,
resultado ou limitação do snapshot técnico foi alterado retroativamente.

## 2. Ciclo remoto comprovado

| Item | Resultado |
|---|---|
| Repositório | AiltonSantanaReis/NeoEng-D-Trace |
| PR | #163 |
| Branch publicada | Ailton/p2d-04 |
| Head da PR | b777cf06209602f3d1a1afe3ca4eebc76e72d3d5 |
| Base anterior | 2007d617ba2ebe9f0171cfd0f8f4263c1cf455ae |
| Estado final da PR | MERGED |
| Merge commit | f55b07b85ef2cf65160f2c10ffac5e63b45732ac |
| Data do merge | 2026-08-30T17:58:12Z |
| Método | merge normal de PR; sem bypass administrativo |
| Tag | não criada |
| Force-push | não realizado |
| Limpeza de untracked | não realizada |

## 3. Checks protegidos

Os dois checks obrigatórios da workflow Private validation passaram no head da
PR:

- test: SUCCESS;
- test-windows: SUCCESS.

Os jobs incluíram verificação do baseline, dependências, lint, formatação,
imports, mypy, auditoria de dependências, scan de riscos, cobertura integrada,
qualidade Stage 4B.5 e verificação de que a árvore de fonte permaneceu
inalterada durante os testes.

## 4. Estado pós-merge reproduzido localmente

- branch local: main;
- HEAD local: f55b07b85ef2cf65160f2c10ffac5e63b45732ac;
- origin/main: f55b07b85ef2cf65160f2c10ffac5e63b45732ac;
- tracked tree: limpa;
- git diff --check: PASS;
- untracked locais: preservados e fora da qualificação.

O ciclo local que antecedeu o merge registrou 1842 passed, 2 skipped, 90,83%
de cobertura de linhas e aprovação da política integrada de branches.

## 5. Limites desta evidência

Este adendo comprova publicação e sincronização Git de P2D-04. Não amplia o
escopo funcional aceito, não declara o editor de cenários completo, não prova
tilemap, colisão própria, NavMesh, entidades/prefabs, iluminação, partículas,
VFX, vetorização ou suporte 3D, e não substitui a decisão e as evidências de
P2D-05 ou dos workstreams futuros.
