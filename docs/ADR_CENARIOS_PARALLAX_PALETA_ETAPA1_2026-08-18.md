# ADR — Baseline de cenários parallax e paleta de comandos

**Status:** aceito para a Etapa 1 — caracterização, sem implementação de produto
**Data:** 18 de agosto de 2026
**Plano:** `docs/PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md`

## Contexto confirmado

O baseline funcional de código é o merge da PR #92,
`b6549ffc1f0e92fb8eeb0f7846414356172191a8`. O HEAD atual do `main` também
contém a reconciliação documental da PR #93, merge
`45b99f058601092a6121a7db4153ba27795325c0`; essa PR não alterou código
funcional. A distinção é obrigatória para não confundir baseline funcional com
HEAD documental.

O projeto atual possui schema de projeto v1, objetos com transformação 3D
persistida e `position.z` já usado pelo modelo e pelo display de transformação.
Também possui ações Qt distribuídas entre menus e barras de ferramentas, além
de histórico Undo/Redo pelo `CommandManager`. A paleta de comandos ainda não é
um contrato existente.

## Decisões

1. A paleta futura reutilizará as `QAction` existentes como fonte única de
   execução; não haverá segunda implementação de comandos.
2. A paleta não removerá menus, atalhos, estados desabilitados, confirmações ou
   transações de Undo/Redo.
3. O cenário futuro será um documento lateral versionado e referenciado ao
   projeto por hash. O schema v1 não será alterado silenciosamente.
4. A profundidade usada pelo parallax será separada do `position.z`/`z_depth`
   já exportado para Godot e Unity até existir ADR de migração explícita.
5. A Etapa 1 entrega apenas baseline, inventário e testes de caracterização.
   Nenhuma paleta, câmera, parallax, overlay ou schema novo é implementado
   nesta etapa.

## Critérios de saída

- baseline e HEAD documental identificados por SHA;
- contratos atuais comprovados por testes executáveis;
- decisões de compatibilidade registradas;
- evidência hashada com comandos e resultados reais;
- suíte existente sem regressão;
- árvore limpa antes do commit.

## Fora do escopo desta etapa

Não fazem parte desta entrega registro de comandos, `Ctrl+K`, interface de
busca, matemática de câmera, documento lateral, preview, exportação ou
integração adicional com engines.
