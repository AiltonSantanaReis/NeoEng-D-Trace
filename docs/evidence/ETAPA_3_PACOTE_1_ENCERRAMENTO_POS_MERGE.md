# Evidência — Etapa 3 / Pacote 1: encerramento pós-merge

## Identificação

- Etapa: `3 — Persistência versionada e confiável`
- Pacote: `1 — Formato de projeto v1, round-trip, migração e escrita atômica`
- Pull request funcional: `#11`
- Commit funcional aprovado: `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`
- Merge commit funcional: `4a45e9c396da6cd63f44f1cf9792526c305478ec`
- Branch validada depois do merge funcional: `main`
- Workflow pós-merge funcional: `#41` (`30672598358`)
- Data de geração: `2026-07-31T23:28:57.508511-03:00`
- Responsável: Ailton Santana Reis

## Objetivo

Registrar permanentemente a validação executada antes e depois da integração da
PR funcional `#11`, reproduzindo o processo de encerramento utilizado nas
Etapas 1 e 2.

Este documento não substitui a evidência funcional. Ele complementa:

- `docs/evidence/ETAPA_3_PACOTE_1_PERSISTENCIA_VERSIONADA.md`;
- `docs/evidence/ETAPA_3_PACOTE_1_EVIDENCE_MANIFEST.json`;
- `docs/evidence/raw/NeoEng-D-Trace_Etapa3_Pacote1_Raw_Evidence_Bundle.zip`;
- `docs/evidence/raw/NeoEng-D-Trace_Etapa3_Pacote1_PostMerge_Main_20260731_232857.zip`.

## Estrutura do merge funcional

- base: `0ff7e66767cedd0ad949a86fc8dae476d7c6594c`;
- commit funcional inicial: `349e2869623d70a23882d08135c770d30cd38fb3`;
- correção de segurança e HEAD aprovado: `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`;
- merge commit: `4a45e9c396da6cd63f44f1cf9792526c305478ec`;
- integração por merge commit;
- squash: não utilizado;
- rebase: não utilizado;
- auto-merge: não utilizado;
- `main` validada no merge commit esperado.

## Gate da PR funcional

- Run `#40` (`30672383923`): `completed/success`;
- Linux: Job `91292624183`, `success`;
- Windows: Job `91292624143`, `success`;
- `212` testes aprovados em cada sistema;
- cobertura `0.4992`;
- baseline `222` antes e depois;
- compilação, lockfile, lint fatal, Black, isort e mypy aprovados;
- artefatos íntegros e não expirados.

## Gate pós-merge funcional da `main`

- Run `#41` (`30672598358`): `completed/success`;
- commit: `4a45e9c396da6cd63f44f1cf9792526c305478ec`;
- Linux: Job `91293265047`, `success`;
- Windows: Job `91293265003`, `success`;
- `212` testes aprovados em cada sistema;
- cobertura `4617` de
  `9249` linhas;
- artefatos reabertos e comparados com seus digests.

## Evidência bruta preservada

Pacote bruto:

- arquivo: `NeoEng-D-Trace_Etapa3_Pacote1_Raw_Evidence_Bundle.zip`;
- tamanho: `1753510 bytes`;
- SHA-256: `411981900d5f3c795e0336a4a813bfe4311d25f647cb6a878b8f7239c2311d8f`.

O pacote contém metadados canônicos da PR, commits, comparação de refs, reviews,
comentários, runs, jobs, artefatos, logs completos por job, os quatro ZIPs
originais do GitHub e checksums internos.

Pacote pós-merge:

- arquivo: `NeoEng-D-Trace_Etapa3_Pacote1_PostMerge_Main_20260731_232857.zip`;
- tamanho: `2542880 bytes`;
- SHA-256: `f8ce9be99ceae4e9859acff3e9f1f967a5c35edca85288a4b0032e6e8f4caaf0`.

O pacote contém os resumos canônicos, o pacote bruto e o conteúdo reaberto dos
artefatos Linux e Windows da `main`.

## Resultados comprovados

- persistência versionada v1 implementada;
- colisões personalizadas e Béziers preservados no round-trip;
- migração legada explícita;
- saves determinísticos;
- escrita atômica preserva o destino anterior em falha;
- entradas desconhecidas, malformadas e incompatíveis rejeitadas;
- limite de arquivo aplicado e testado; limites de objetos e pontos
  implementados, sem teste explícito das fronteiras neste pacote;
- path traversal relativo bloqueado após revisão;
- CI real em Linux e Windows aprovado antes e depois do merge.

## Riscos residuais

- `R-002`, `R-003`, `R-004`, `R-005`, `R-006`, `R-008`, `R-011`, `R-012` e
  `R-013` permanecem abertos;
- `R-007` permanece aberto para as validações geométricas que não pertencem a
  este pacote;
- os `125` achados não bloqueantes do Flake8 permanecem registrados;
- a cobertura global continua em aproximadamente `50%`;
- mypy ainda informa que corpos de funções não tipadas não são verificados por
  padrão;
- avisos de depreciação do Poetry e das actions Node 20 permanecem não
  bloqueantes, mas devem ser tratados em manutenção futura.

## Limites da aprovação

A aprovação cobre somente o Pacote 1 da Etapa 3. Não cobre UI Abrir/Salvar,
release Windows, ausência de bugs, segurança integral, qualidade geométrica
completa ou conclusão de toda a Etapa 3.

## Decisão

**APROVADO — PACOTE 1 APTO AO ENCERRAMENTO FORMAL APÓS A INTEGRAÇÃO DESTE
REGISTRO E A VALIDAÇÃO FINAL DA `main`**

O Pacote 2 da Etapa 3 não deve começar antes da integração desta PR documental
e do CI pós-merge final.
