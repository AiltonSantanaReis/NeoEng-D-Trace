# Plano de Cenários Parallax e Paleta de Comandos — NeoEng-D-Trace

**Data de aceitação:** 18 de agosto de 2026
**Estado:** CONCLUÍDO NO ESCOPO APROVADO — Etapas 4A a 4B.5 integradas pela PR `#99`; CI pós-merge aprovado no run `32184900502`
**Baseline funcional verificada:** `a129cd251345456c39254b39682d1ef083fd28d0` (merge da PR `#99`)
**Candidato local 4B.5 verificado:** `36aaef4` (commit da PR `#99`, integrado no merge acima)
**Fonte de referência:** `plano_cenarios_parallax_neoeng_dtrace.docx`, SHA-256 `066dd9a5b192e215b1859a81ab22fbdfe2d9a7b8db46acbc7f6f62fe867cc0ac`

## Natureza deste documento

Este plano registra uma decisão de produto aceita. A câmera/parallax matemática (4A), o schema lateral (4B.1), o preview/overlays (4B.2), a autoria lateral (4B.3), a exportação/validação real (4B.4) e o fechamento de qualidade (4B.5) possuem implementação, evidência local hashada, merge na PR `#99` e CI pós-merge aprovado no run `32184900502`.
O documento anexado é uma especificação de referência; o status acima e as evidências próprias de cada etapa são a autoridade para o estado atual. Suas
afirmações sobre WebGL, runtime, shaders, partículas e desempenho não são
afirmações sobre o estado atual do projeto.

## Escopo aceito

Serão avaliadas duas funcionalidades novas:

1. paleta de comandos integrada ao editor existente;
2. módulo opcional de autoria e preview de cenários 2D/2.5D com parallax,
   câmera e molduras seguras.

O módulo não transforma o NeoEng-D-Trace em editor de imagens, engine de jogos
ou runtime completo. Partículas, shaders, pós-processamento, triggers,
streaming de texturas e SDK de reprodução permanecem fora do primeiro MVP e
exigem decisão e contratos próprios antes de qualquer implementação.

## Regras de compatibilidade

- O schema de projeto v1 e o significado atual de `SceneObject.position.z` não
  serão alterados silenciosamente.
- A profundidade de parallax será um conceito separado do `z_depth` de
  exportação Godot/Unity.
- A primeira integração usará um documento lateral de cenário versionado,
  referenciado por hash ao projeto `.ndtproj`; a migração para o schema principal
  só poderá ocorrer por ADR e migração explícita.
- A paleta reutilizará as `QAction` existentes como fonte única de execução;
  menus tradicionais permanecerão disponíveis.
- Nenhuma ação da paleta poderá ignorar estado desabilitado, confirmação,
  bloqueio de camada ou transação de Undo/Redo.

## Ordem obrigatória de implementação

1. Baseline, ADR, inventário de contratos e testes de caracterização.
2. Registro de comandos, IDs estáveis, estados habilitado/desabilitado e
   integração de `Ctrl+K`.
3. Interface da paleta, busca, teclado, Escape, localização e acessibilidade.
4. Testes de regressão da paleta, menus, atalhos e ações bloqueadas.
5. Modelo matemático puro de câmera ortográfica, profundidade e parallax.
6. Schema lateral de cenário, limites, hashes, round-trip e rollback.
7. Preview no canvas e overlays de aspect ratio/safe area sem alterar o modo
   normal de edição.
8. Painel de camadas de cenário, inspetor, Undo/Redo e persistência completa.
9. Exportação JSON genérica e validação real dos consumidores Godot/Unity — concluída no escopo 4B.4, com diferenças de capacidade documentadas.
   respeitando diferenças de capacidade documentadas.
10. Benchmark Windows, determinismo, regressão, evidências hashadas, CI,
    revisão do diff, PR e merge — concluída no escopo aprovado; o CI pós-merge
    do `main` foi aprovado em Linux e Windows.

## Gates de cada etapa

Uma etapa somente será encerrada quando a implementação do seu escopo estiver
completa, sem pendências internas, com testes positivos e negativos, evidência
reproduzível, hash dos artefatos, cobertura sem redução, verificação de árvore
limpa e decisão formal. `PARCIAL`, `NÃO TESTADO` e `BLOQUEADO` não autorizam a
etapa seguinte.

Antes de cada commit serão executados os gates aplicáveis do repositório. Após
a conclusão comprovada de cada etapa, será feito commit e push da etapa. O PR
somente será promovido e mesclado depois dos checks obrigatórios e do CI
pós-merge correspondente. Não será usado force push, force merge, skip,
xfail, alteração de regra ou bypass para produzir aprovação.

## Evidências obrigatórias

Cada etapa deverá registrar em `docs/evidence/` o commit/HEAD, branch,
ambiente, comandos, entradas e hashes, resultados brutos, cobertura, falhas,
limitações, rollback e decisão. Testes de engine deverão usar fixtures e
processos reais quando o comportamento da engine for o objeto da validação.

## Critério de não regressão

O modo atual de edição 2D, o schema v1, os exportadores existentes, o gizmo,
camadas, grupos, Undo/Redo, menus, atalhos e integrações Godot/Unity devem
continuar funcionando. Qualquer regressão, divergência documental ou artefato
não reproduzível interrompe a etapa até a causa raiz ser corrigida.
