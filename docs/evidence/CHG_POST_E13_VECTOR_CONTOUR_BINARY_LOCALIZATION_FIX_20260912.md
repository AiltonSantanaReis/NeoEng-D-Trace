# Correção pós-E13 — status PT-BR do contorno vetorial no binário

**ID:** `CHG-POST-E13-VECTOR-CONTOUR-BINARY-LOCALIZATION-FIX-20260912`

**Versão:** `1.0`

**Data:** `2026-09-12`

**Estado:** `PASS`

**Commit de produto:** `c0989cd3049f2692805bd51ac20dfaf939d7fe76`

**Commit da build:** `eea7b6ccdf4ec1258bb3932cba7a2db8d84a5403`

**Checkpoint protegido:** `ec94530fcba39be3bbce0439fc56aa48957442c0`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Objetivo e fronteira

Requalificar no executável distribuível a falha localizada no lote anterior:
em PT-BR, o painel de contorno vetorial exibia mensagens de operação em
inglês. O escopo desta mudança é somente a seleção de idioma dessas mensagens;
detecção, edição, criação, persistência e contratos de inglês foram mantidos.

O lote antigo não foi sobrescrito. A auditoria geral do Editor de Cenário,
incluindo câmera, luz, partículas, tilemap/tileset, engines e UX aberta,
continua sendo acompanhada pelo registro de localização/contexto e não é
implicitamente encerrada por este PASS restrito.

## Build e proveniência

- Diretório: `build/post-e13-localization-build-20260912-r1/`;
- executável: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- tamanho: `10.876.520` bytes;
- SHA-256 do executável:
  `96053F3334CB114E9AF1BA156209D3F6E65F5EEA06FD67165B0A773A1BC92F4B`;
- versão de arquivo/produto: `0.3.0`;
- idioma do recurso Windows: `Português (Brasil)`;
- `continuity-provenance.json`: `status=PASS`, source commit `eea7b6c`;
- smoke portátil oficial: `PASS`, com `portable-smoke-report.json` no mesmo
  diretório de build.

A build foi executada pelo procedimento oficial de Windows com o wrapper de
preservação de não rastreados. Os artefatos de auditoria foram movidos para um
diretório temporário, a árvore limpa foi validada e todos foram restaurados no
`finally`; nenhum arquivo de evidência foi apagado.

## Fluxo Win32 real

Script: `scripts/capture_e03_asset_library_binary.ps1`
Pacote: `artifacts/audit-post-e13-binary-vector-contour-20260912-r3/`
Manifesto de capturas: `artifacts/audit-post-e13-binary-vector-contour-20260912-r3/manifest.json`
SHA-256 do manifesto:
`67CC4848E40EF23406214FC060043A61D86B7EA421CB7FB438D8AF14D6CED03A`

O script abriu o executável novo com `--open-project-gui` e
`--open-scenario-editor-gui`, encontrou a janela por PID/título, enviou
cliques e teclas Win32, capturou a janela com `PrintWindow` e verificou os
arquivos persistidos após salvar/recarregar. CUA nativo não estava disponível
nesta sessão; o fallback Win32 está declarado, não tratado como CUA.

| Passo | Captura | SHA-256 | Resultado observado |
|---|---|---|---|
| entrada e projeto | `01-main.png` | `94F26FE3A7DBA7BC1771CC62D17F9D0EB664FD248440C76CA64D3A154D5995D0` | janela real do editor canônico localizada |
| projeto carregado | `03-main-after-project-load.png` | `7184A27AD3B6DD15D64BCB1B91E51E8A35EAB3E94DA2CF857301E4F3AFE403A8` | biblioteca e viewport disponíveis |
| entrada vetorial | `06-vector-contour-initial.png` | `4BA5522B1DCAD05AF571CC52427335CDDCE8343F0CD0C2169B8F150746FCF8C0` | ferramenta `Contorno vetorial` em PT-BR |
| asset selecionado | `08-vector-library-selected.png` | `8ACB151D072BC219289E06189AF9E83EDC0A50B45EB2FC1CADA3583187961261` | `vector-source` selecionado |
| detecção | `11-vector-contour-detected.png` | `25228B72E61E69DAC46566B1DE0AE458838776D3B2E218EF65C7D632F4B8A611` | `Contorno detectado para vector-source: 4 vértices` |
| correção de vértice | `12-vector-contour-edited.png` | `0C8EF5E3D211A81CB9D6C375CF18C3AA28E198D2A9FB52704190FF5BA27601A8` | `Vértice do contorno corrigido`; X/Y editados para `-5,00` |
| criação | `13-vector-contour-created.png` | `52C852D785F3B2412204B37A38C970A3021DCFDDCC2E49065B5682111E6FFB27` | `Objeto vetorial de cena criado: vector_vector-source` |
| salvar | `14-vector-contour-saved.png` | `A40965228014EB3C5875CF7B2409DA3968EE757A3D60DA3FB9D0FF5AB3AEC7E` | `Cenário salvo` |
| reabrir | `15-vector-contour-reloaded.png` | `792244DAA3B09B208FB1900868D6A7A68C9208C77D881D0C631E6750F66360B0` | `Cenário recarregado`; objeto reaparece |

As capturas 11, 12 e 13 foram inspecionadas visualmente: o texto PT-BR está
na barra de status da própria janela do executável, enquanto o painel e os
controles continuam operacionais.

## Persistência observada

Arquivo: `artifacts/audit-post-e13-binary-vector-contour-20260912-r3/vector-contour-fixture/vector-contour.ndtscene.json`
SHA-256:
`EC8CFF2F2A8BA79A08254224B064BFEA0957E832E4A4F52E52C4FBAA7A4CF393`

Após o round-trip:

- `objects=1`;
- `vector_geometry.algorithm=opencv-contour-tree-r1`;
- `polygon_vertices=4`;
- `collision_vertices=4`;
- `source_sha256=4bffd31518cb8eabcfba2b2a4379ba54d6a1632ebd8836b1cbae36f9b33a9a18`.

## Verificação de regressão

Execução focada sem `skip`, `xfail` ou filtro para fabricar aprovação:

```text
73 passed in 12.55s
```

O conjunto cobriu localização/tooltips, viewport, paralaxe, separação dos
editores, auditoria funcional, regressões de UI e todo o conjunto de contratos
vetoriais E09. O smoke oficial da build também passou. A suíte completa do
repositório e a requalificação das demais funcionalidades permanecem etapas
separadas.

## Resultado e limites

`PASS` para o requisito `LOC-POST-E13-01` no escopo do binário: os status de
detecção, edição e criação agora aparecem em PT-BR na build nova; o fluxo
Win32, salvar/recarregar e os dados hash-bound foram observados.

Não é PASS para:

- o disparo automático de tooltip, que permanece `PENDING_EVIDENCE` conforme
  `AUDITORIA_POST_E13_LOCALIZACAO_CONTEXTO_20260912.md`;
- caminhos menos frequentes ainda não exercitados no binário;
- equivalência de runtime Godot/Unity;
- revisão humana final, gizmo, produção de modelos ou encerramento da
  auditoria pós-E13.
