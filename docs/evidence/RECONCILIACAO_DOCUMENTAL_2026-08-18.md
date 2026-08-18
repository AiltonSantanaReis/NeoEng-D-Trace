# Evidência — Reconciliação documental e registro do plano

## Identificação

- Commit funcional de referência: `b6549ffc1f0e92fb8eeb0f7846414356172191a8`
- Branch de trabalho documental (identificador omitido do artefato publicado).
- Data: 18 de agosto de 2026
- Escopo: documentos vivos, matriz de riscos, índice de evidências, changelog e
  registro do plano aceito; nenhum código funcional foi alterado.

## Objetivo

Alinhar os documentos vivos ao estado real do `main` após a PR `#92`, preservar
snapshots históricos e registrar o plano aceito de paleta de comandos e
cenários parallax como `PLANEJADO / NÃO INICIADO`.

## Entradas

- Documento de referência: `plano_cenarios_parallax_neoeng_dtrace.docx`
- SHA-256 da entrada: `066dd9a5b192e215b1859a81ab22fbdfe2d9a7b8db46acbc7f6f62fe867cc0ac`
- `main` e `origin/main` antes da etapa: `b6549ffc1f0e92fb8eeb0f7846414356172191a8`

## Comandos e validações executados

- confirmação de `git status`, `HEAD` local e `origin/main`;
- leitura estrutural do DOCX com `python-docx` e inspeção do pacote OOXML;
- tentativa do renderer oficial `render_docx.py --emit_pdf`;
- testes de caracterização e regressão: `91 passed`;
- suíte completa local: `1202 passed, 2 skipped, 10 warnings`;
- testes de baseline e integridade de evidências incluídos na suíte completa: aprovados;
- CIs já vinculados ao estado funcional: pré-merge `32107519574` e pós-merge
  `32107883246`, ambos com Linux e Windows em `success`;
- substituições documentais protegidas por contagem exata de ocorrência;
- nenhum arquivo de código, fixture funcional, teste ou regra de CI foi
  removido ou alterado.

## Resultado

- Documentos vivos receberam a âncora do merge da PR `#92` e a distinção entre
  a release `v0.2.0` publicada e o `main` posterior.
- O novo plano foi registrado com dez etapas, gates, rollback, evidências e
  política de commit/push por etapa.
- A matriz de funcionalidades e a matriz de riscos classificam as duas novas
  funcionalidades como `PLANEJADAS / NÃO INICIADAS`.
- O plano de adaptadores Godot/Unity foi explicitamente separado do plano de
  cenários; a PR `#92` não foi usada para promover nenhuma etapa de engine.

## Limitações

- A inspeção visual do DOCX ficou `NÃO TESTADA`: o renderer oficial não
  encontrou o conversor PDF necessário neste ambiente. A análise textual e
  estrutural foi concluída sem modificar o original.
- A existência do plano não comprova implementação, integração, desempenho ou
  compatibilidade nas engines.

## Decisão

`APROVADO` para a reconciliação documental desta etapa. As funcionalidades
novas permanecem explicitamente `PLANEJADAS / NÃO INICIADAS` e não autorizam
promoção funcional, release ou declaração de integração.
