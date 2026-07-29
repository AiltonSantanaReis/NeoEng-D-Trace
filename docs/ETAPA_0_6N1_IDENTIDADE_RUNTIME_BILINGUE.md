# Etapa 0.6N1 — Identidade central e runtime bilíngue

**Base obrigatória:** 0.5.2F3 + 0.6R validada pela 0.6R1.  
**Natureza:** migração isolada de identidade; nenhuma alteração algorítmica.  
**Nome ativo:** NeoEng-D-Trace.

## Objetivo

Executar a Fase R1 do plano de renomeação e a parte estritamente relacionada à identidade da Fase R2:

- criar uma fonte única de identidade;
- migrar superfícies de runtime que exibiam PolygonTool;
- preservar inglês e português na janela principal;
- manter formato de projeto, configuração e pacote estrutural fora desta etapa;
- impedir substituição cega em documentação histórica.

## Arquivos funcionais alterados

- `app.py`;
- `src/core/app_identity.py` (novo);
- `src/core/logger.py`;
- `src/ui/main_window.py`;
- `src/exporters/gltf_exporter.py`;
- quatro benchmarks;
- três perfis de exportação (somente docstrings);
- `src/ui/export_preview.py` e `src/ui/theme_qss.py` (somente docstrings);
- `tools/run_legacy_tests.py`.

## Garantias de compatibilidade

- imports permanecem em `src.*`;
- `pyproject.toml` mantém temporariamente o nome de distribuição legado até a Fase R3;
- configuração continua em `config.json` até a Fase R4;
- formato de projeto não recebe identificador inventado;
- geometria GLTF, buffers, índices e metadados de objetos não são alterados; somente o campo `asset.generator` muda;
- JSON e TXT de colisões preservam a estrutura anterior;
- os quatro hashes críticos da 0.5.2F3 devem permanecer idênticos.

## Bilíngue

Foram cobertos em inglês e português:

- título da janela principal;
- título com arquivo carregado;
- abrir imagem e filtro de imagens;
- exportação principal;
- exportação de colisão JSON/TXT;
- ajustar visão e pixel 1:1;
- Lit/Iluminado e três modos X-Ray/Raio-X;
- foco, limpar, menus Edit/View e seletor de idioma.

As lacunas anteriores fora da janela principal não foram escondidas e estão registradas em `INVENTARIO_LOCALIZACAO_0_6N1.md`.

## Correção de defeito observada

`MainWindow.export_collision_txt` continha duas funções aninhadas e inalcançáveis, duplicando os exportadores de colisão. Elas foram removidas. Os métodos públicos existentes e os formatos de saída foram mantidos.

## Fora do escopo

- migração para pacote `neoeng_d_trace`;
- AppData e migração de configuração;
- schema e migração de projeto;
- executável, instalador, ícones e build;
- tradução integral de todos os diálogos;
- refatoração de domínio ou algoritmos.

## Portões obrigatórios

1. estado 0.6R confirmado;
2. índice Git vazio, nenhum remote e identidade `noreply` correta;
3. hashes anteriores dos arquivos-alvo conferidos;
4. compilação sintática;
5. testes de identidade sem Qt;
6. testes Qt de inglês e português no Windows;
7. 28 testes da 0.5.2F3;
8. suíte oficial completa;
9. busca por referências legadas de runtime fora da allowlist;
10. rollback integral.
