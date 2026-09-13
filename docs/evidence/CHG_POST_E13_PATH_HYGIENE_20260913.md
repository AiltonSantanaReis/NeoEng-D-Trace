# Registro de mudança — higiene de caminhos documentais

**ID:** CHG-POST-E13-PATH-HYGIENE-20260913
**Status:** `PASS`
**Data:** 2026-09-13
**Escopo:** `docs/CONTROLE_CONTINUIDADE_ATUAL.json` e auditoria de desempenho

## Constatação

A primeira regressão oficial segura após a correção dos warnings detectou uma
falha no contrato `test_tracked_files_and_nested_archives_have_no_prohibited_references`:
dois documentos rastreados continham caminhos absolutos do usuário do host.
Isso era um problema de higiene/rastreabilidade documental, não do produto,
mas impedia a suíte de passar.

## Correção

Os caminhos absolutos foram convertidos para referências relativas ao checkout,
preservando os mesmos diretórios e os hashes dos artefatos. Nenhum arquivo foi
removido, nenhum hash de executável foi alterado e nenhuma evidência histórica
foi apagada. A detecção foi corrigida de forma fail-closed pela própria suíte.

## Verificação

- O teste de higiene deve passar isoladamente antes da suíte completa.
- A suíte oficial deve ser executada sem filtros, com symlink bloqueado no host
  pela variável ausente e com os testes reais de symlink reservados ao sandbox.
- O pacote Linux anterior com 19 falhas permanece em
  `artifacts/audit-post-e13-official-suite-safe-20260913-r1/`.

## Dependências e governança

- [GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [CHG_POST_E13_CONTROLLED_DANGEROUS_TESTS_20260913.md](CHG_POST_E13_CONTROLLED_DANGEROUS_TESTS_20260913.md)
- [CONTROLE_CONTINUIDADE_ATUAL.json](../CONTROLE_CONTINUIDADE_ATUAL.json)
