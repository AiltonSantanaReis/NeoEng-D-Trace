# Plano Mestre de Estabilização — NeoEng-D-Trace

Baseline oficial: `a3f376af2a1f738bb36c107320757d0339300c78`.

## Regras inegociáveis

1. `main` representa somente estados aprovados.
2. Nenhuma afirmação de sucesso sem evidência reproduzível.
3. Estados permitidos: APROVADO, REPROVADO, BLOQUEADO, NÃO TESTADO e PARCIAL.
4. NÃO TESTADO, BLOQUEADO e PARCIAL nunca equivalem a APROVADO.
5. É proibido remover, enfraquecer, ignorar ou maquiar teste para obter resultado verde.
6. Toda falha corrigida exige teste de regressão.
7. Nenhuma etapa avança com perda de dados, regressão, build quebrado, comportamento não determinístico ou evidência insuficiente.
8. Funcionalidade nova fica congelada até a conclusão dos bloqueadores de estabilização.

## Definição de concluído

Uma tarefa somente termina quando possuir requisito objetivo, reprodução anterior, causa raiz, implementação completa, testes unitários e de integração, testes de UI quando aplicáveis, cenários negativos, cobertura sem redução, compilação, lint, tipagem, documentação, evidências e revisão do diff.

## Evidências obrigatórias

Cada etapa deve registrar:

- commit testado;
- sistema operacional e Python;
- dependências instaladas;
- comandos completos;
- quantidade de testes aprovados, reprovados, ignorados e bloqueados;
- cobertura por módulo;
- hashes de entradas e saídas relevantes;
- limitações e riscos residuais;
- conclusão formal.

Os relatórios permanentes ficam em `docs/evidence/`. Resultados brutos devem ser publicados como artefatos do CI.

## Estratégia de testes

- unitários para domínio e serviços;
- propriedades para invariantes geométricos e round-trip;
- integração com arquivos temporários reais;
- UI com `pytest-qt`;
- ponta a ponta para importar, editar, salvar, reabrir e exportar;
- compatibilidade em Windows 11 e Linux;
- segurança para entradas malformadas, limites e permissões;
- desempenho com baseline reproduzível.

## Metas de cobertura

- nenhum módulo operacional em 0%;
- 100% dos fluxos críticos mapeados;
- persistência, Undo/Redo e exportadores: 95% de linhas e 90% de branches;
- núcleo geométrico: 90% de linhas e 85% de branches;
- cobertura global: 90% de linhas e 85% de branches;
- exclusões somente com justificativa explícita.

## Ordem obrigatória

0. Governança e proteção da baseline.
1. Ambiente reproduzível e CI Windows/Linux.
2. Inventário funcional e testes de caracterização.
3. Persistência e contrato versionado de projeto.
4. Ciclo Abrir/Salvar na interface.
5. Undo/Redo completo.
6. Exportação de colisões.
7. CLI e modo headless.
8. Bézier e geometria.
9. Física, colisão e APIs duplicadas.
10. Exportadores e validação nas engines declaradas.
11. Cobertura integral da interface.
12. Segurança e limites operacionais.
13. Refatoração protegida por testes.
14. Build Windows, auditoria final e candidato a release.

Nenhuma etapa pode ser pulada. Retorno a uma etapa anterior deve ser registrado como lacuna ou regressão descoberta.
