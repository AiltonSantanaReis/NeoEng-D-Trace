# Evidência P2D-05 — fronteira de implementação

**Data:** 30/08/2026 (UTC-03)
**Decisão:** P2D-05 ACEITO — contrato de performance, limites, formatos e erros
**Estado:** implementação controlada autorizada; qualificação, commit e publicação pendentes

## Prova de entrada

| Item | Resultado |
|---|---|
| Repositório | raiz local do repositório compartilhado |
| Branch de trabalho | `p2d-05-quality-hardening` |
| Base de produção/rollback | `f55b07b85ef2cf65160f2c10ffac5e63b45732ac` |
| Commit documental presente na branch | `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3` |
| Tracked tree antes da implementação | limpa |
| Suíte de entrada | `1842 passed, 2 skipped, 1 warning` |
| Python | 3.11.9 da `.venv` |
| Escopo remoto | não autorizado nesta fase |

O commit documental posterior à base não altera código de produto. A branch
foi mantida sobre o estado atual de `main` para preservar o contrato aceito;
qualquer comparação de produto usará explicitamente a base `f55b07b8` e
separará documentação de produção.

## Implementação permitida

### Produção

- `src/core/logger.py`: privacidade idêntica em stream e arquivo.
- `src/persistence/scene_authoring_io.py`: limite de bytes na serialização
  canônica e no save.
- `src/exporters/scene_authoring_export.py`: limite de bytes antes da escrita
  de qualquer export.
- `src/persistence/p2d05_errors.py`: códigos e mensagens seguras, acionáveis e
  reproduzíveis para as falhas existentes.
- Handlers do editor profissional e do painel de assets: uso desse
  classificador sem alterar ações, estados válidos, layout ou geometria.

### Qualificação

- testes unitários/negativos e de integração no novo arquivo
  `tests/test_p2d_05_quality_contract.py`;
- benchmark reproduzível em `scripts/benchmark_p2d_05.py`;
- auditoria de privacidade e integridade em
  `scripts/audit_p2d_05_evidence.py`;
- evidências correntes e atualização do plano vivo.

## Imutáveis

Não podem mudar neste lote:

- valores de `src/core/operational_limits.py`;
- schemas, versões, IDs e migração explícita V1→V2;
- bytes canônicos, ordenação e hashes;
- remoção de `source_path` do export portátil;
- mapeamentos genérico/Godot/Unity, orientação, escala, pivot e flip;
- recovery válido, atomicidade e preservação do último arquivo válido;
- QAction, atalhos, árvore de widgets, geometria, G/V/B, C3 e baselines;
- editor legado, linhas independentes e integrações de engine.

## Gate da fronteira

O lote será interrompido e reaberto como nova decisão se precisar alterar
qualquer arquivo, símbolo, limite, schema, formato, comportamento de sucesso,
geometria, runtime ou linha independente não listada acima. Nenhum commit,
build, push, tag, merge ou release é autorizado por este registro.

O próximo registro esperado é o relatório de implementação/precommit, com os
resultados reais da execução corrente; números, hashes, caminhos de artefatos e
decisões não serão copiados de outra execução.
