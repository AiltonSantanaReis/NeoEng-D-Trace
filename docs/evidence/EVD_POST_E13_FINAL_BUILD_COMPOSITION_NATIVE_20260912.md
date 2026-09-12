# Evidência pós-E13 — build final e composição nativa real

**ID:** `EVD_POST_E13_FINAL_BUILD_COMPOSITION_NATIVE_20260912`

**Estado:** `PASS` — checkpoint técnico de build, composição, persistência e recuperação; lote pós-E13 `IN_PROGRESS` e revisão humana `PENDING_EVIDENCE`

**Data:** 2026-09-12

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base auditada da correção:** `dd344f47c1a631729f53a6370759fc449705fd0c`

**Branch da build:** `Ailton/post-e13-final-build-recovery-v4-20260912`

**Mudanças relacionadas:** [`CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md`](CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md) e [`CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md`](CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisões ativas:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md) e [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Requisitos e critérios observados

Esta evidência cobre o checkpoint técnico dos contratos `REQ-F02-EVIDENCE-AUTOMATION`,
`REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`, `REQ-F10-UI-ACCESSIBILITY`
e `TMAP-001/002/003/005`, além da integração `CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912`.
O critério aplicado foi: entrada nativa controlada, operação real, saída
observável, erro reproduzível, recuperação, salvar/reabrir, exportação,
validação de runtime e hashes; nenhuma captura isolada foi tratada como prova
de funcionamento.

## Suíte oficial e commit

- Comando sem filtros: `.venv311\Scripts\python.exe -m pytest -q`.
- Resultado: `2226 passed, 2 skipped, 1 warning` em 2228 testes coletados.
- Log: `artifacts/post-e13-recovery-visible-official-v4-20260912.log`.
- SHA-256 do log: `B1637DEFA413FFF05A5FD463109DB10D5962A563AF39FF0E4DB89C02F7CE2B0B`.
- O warning do teste Qt/depreciação foi preservado no log.
- O teste focal que protege a regressão de layout passou `26 passed` antes da suíte oficial.

## Build limpa e smoke portátil

A build foi feita em checkout separado, diretamente do commit auditado. O
manifesto de proveniência registra `status: PASS`, `source_commit` completo e
o SHA do registro de continuidade no instante da build.

| Artefato | Caminho | Resultado |
|---|---|---|
| Executável GUI | `build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | 8.177.174 bytes; SHA-256 `CBC16B6425158362572848D59D847988F8300455E1AE973DB961A0C2162046A8` |
| Arquivo portátil | `build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912/NeoEng-D-Trace-0.3.0-win64-portable.zip` | 137.405.711 bytes; SHA-256 `D942187979E6BA494256DCA7ADBB2D4FBFCBBAE346FD9D2F55988845028B7C4D` |
| Proveniência | `build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912/continuity-provenance.json` | SHA-256 `2DE581B69E71FD41E68509810C6D7A2F7C5564B3EAA50A62EF4BC73A72A4F2DF` |
| Smoke report | `build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912/smoke/portable-smoke-report.json` | 11/11 checks; `SUCCESS`; SHA-256 `94452D9F6D98F9DD66C0925C549423A40CA35BD2A3E0FF3A022D6C59E881AF33` |
| Log de build | `build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912-build.log` | SHA-256 `2D2AEC5FF2F04D350F9646D7470C9E1F012AC9001FF8756D7ACFF3A00832C855` |

O empacotamento preservou o warning `Hidden import "tzdata" not found!`; ele
não foi ocultado nem convertido em falha ou sucesso artificial.

## Fluxo nativo real executado

O binário portátil foi aberto com o projeto de fixture isolado. A automação
usou entrada Win32 real (`mouse_event`, `keybd_event`, `PrintWindow` e
`CopyFromScreen`) pelo helper versionado
`scripts/capture_independent_scene_binary.ps1`. A CUA do ambiente falhou ao
inicializar com `os error 3`; esse fallback está explicitamente declarado e
não é tratado como CUA bem-sucedida.

Entradas observadas no processo nativo:

1. abrir projeto pela GUI;
2. abrir o Editor de Cenário;
3. exportar composição;
4. salvar cenário;
5. fechar e reabrir;
6. corromper somente o fixture da cena para testar erro;
7. recarregar e observar o estado de recuperação em PT-BR;
8. acionar `Recuperar Último Válido`;
9. salvar novamente;
10. exportar a composição recuperada.

O relatório bruto está em
`build/post-e13-final-build-recovery-v4-20260912/artifacts/post-e13-final-native-composition-recovery-v4-20260912/native-flow-output.json`;
SHA-256 `60EBE0228865C2D6C90F03519753DE88307E1BAE915F61DBA43987AD256F58E6`.
O processo observou a janela `Editor de Cenário — NeoEng-D-Trace` em
`1933x1045` e terminou com `exit 0`.

## Capturas reais e resultado visual

Todas as imagens abaixo são capturas da janela nativa do executável v4; os
hashes são os registrados no relatório do fluxo.

| Etapa | Captura | SHA-256 | Resultado observado |
|---|---|---|---|
| Editor carregado | `composition-01-scenario-editor.png` | `4F259E81810BC8D5B18B8A65987B5085F134DF71EA9C6D045943C372087C2D5C` | Camadas `Z00 Fundo`/`Z01 Frente`, parallax e gizmos visíveis |
| Após exportação | `composition-02-exported.png` | `4F259E81810BC8D5B18B8A65987B5085F134DF71EA9C6D045943C372087C2D5C` | Janela permaneceu estável após a operação |
| Após salvar/reabrir | `composition-03-after-save.png` / `composition-04-after-reopen.png` | `4F259E81810BC8D5B18B8A65987B5085F134DF71EA9C6D045943C372087C2D5C` | Estado visual persistido |
| Erro e recuperação | `composition-05-recovery-prompt.png` | `BE829AA548403F58EA6EC4B553CBCE645DC7056BB4ED7AA6629EE9FDF0C98B3B` | Mensagem PT-BR completa, centralizada e sem cortar; inspetor continua no layout |
| Depois de recuperar | `composition-06-after-recovery.png` | `30F23DA33689C2B6BADE72C7F67ED660E7508BC1B42B728F70FE9D0E8324D909` | Viewport reconstruído |
| Salvar/exportar recuperação | `composition-07-after-recovery-save.png` / `composition-08-exported-after-recovery.png` | `30F23DA33689C2B6BADE72C7F67ED660E7508BC1B42B728F70FE9D0E8324D909` | Persistência e exportação concluídas |

O defeito que motivou o checkpoint foi reproduzido e corrigido: o `sizeHint`
de uma mensagem localizada multilinha fazia o `QSplitter` crescer além da
janela. O commit `dd344f4` limita a largura do estado vazio/recuperável a 720
px, mantendo quebra de linha e o inspetor visível. O teste automatizado exige
essa restrição e o binário v4 comprova o resultado visual.

## Composição, Tilemap e Tileset

O fixture usou o atlas real `source_atlas.png`, 6948 bytes, SHA-256
`4BFFD31518CB8EABCFBA2B2A4379BA54D6A1632EBD8836B1CBAE36F9B33A9A18`, com o
binding seguro `assets/tilesets/scenario/source_atlas.png` no tilemap.

| Artefato | Resultado |
|---|---|
| `exports/composition-e11/composition.json` | SHA-256 `EB53DFF5E71EE1F6BC338F3027A8C98D0526ED5E6E23D3050443B0FBECD51E2E`; capability `tilemap-runtime: emitted-hash-bound` |
| `exports/composition-e11-r2/composition.json` | Mesmo SHA do manifesto após recuperação |
| `tilemap-runtime/tilemap-runtime.json` | 2030 bytes; SHA-256 `B1F95AD22750D5ADC4CB2A331B241F822387CC5A2A8BC30C65B463A0E824BB93`; 4 células, 1 camada, 1 tile e atlas hash-bound |
| Origem do tilemap | SHA-256 `16285E090B4B49F2C1B0409DB7B559AD08C1F103669B2654AF61A7A17ED7F25C` |
| Cena após salvar/recuperar | SHA-256 `1A5555F380BC7B98F7CD14AB73FB0D5BF763C336C15BA0A80D7B8FAB023FE000` |
| Sidecar de recuperação | SHA-256 `7DE0CACFFDBBA42B11B1EB427ADB3E5E6029E8FA1FF7ACC3BA856CFE3005C4A9` |

`validate_composition_package` revalidou os dois pacotes completos com
`COMPOSITION_VALIDATION=PASS`. A validação incluiu hashes de todos os
componentes, schema do tilemap, payload runtime e binding do atlas.

## Falhas históricas preservadas

- A primeira tentativa de exibir a recuperação produziu uma captura igual ao
  estado normal e continua preservada no pacote histórico.
- As versões v2 e v3 exibiram a mensagem, mas com o texto cortado; a captura
  v3 permanece em
  `../post-e13-final-build-recovery-v3-20260912/artifacts/post-e13-final-native-composition-recovery-v3-20260912/composition-05-recovery-prompt.png`
  com SHA-256 `112B91FD07D4ABEE7CE776C9F2967CB3D2DBC5FAA9CD64AAF2CD5927916924D1`.
- A correção v4 produziu nova captura `BE829...`; nenhuma baseline anterior foi
  sobrescrita ou removida.

## Limitações e estado de fechamento

- O fallback de captura é Win32 porque CUA não inicializou neste ambiente.
- O warning de empacotamento `tzdata` permanece aberto como warning ambiental.
- O viewport híbrido 3D continua documentado como `VERTICAL_SLICE_ONLY`; o
  gate técnico externo Godot/Unity está separado e aprovado, mas isso não
  equivale a afirmar que o editor é um DCC 3D completo.
- Esta evidência fecha tecnicamente build, composição geral, Tilemap/runtime,
  persistência e recuperação. Não promove captura automatizada a aceite humano.
- A revisão humana final permanece `PENDING_EVIDENCE` por decisão explícita;
  o lote pós-E13 continua `IN_PROGRESS` até a auditoria/aceite final. E13
  permanece congelado e histórico.
