# Registro de evidência pós-E13 — contorno vetorial no binário

**ID:** `CHG-POST-E13-VECTOR-CONTOUR-BINARY-AUDIT-20260912`

**Estado:** `PASS_TECNICO / UX_REFINEMENT_OPEN`

**Data:** 2026-09-12

**Commit auditado:** `6f6ecf1` (harness com round-trip adicionado após a
requalificação de materiais)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Escopo

Executar no executável Windows real o fluxo de contorno vetorial: abrir a
ferramenta, selecionar um asset raster, detectar o contorno, editar um vértice,
criar o objeto vetorial, salvar, recarregar e verificar o documento persistido.
O lote inicial permanece preservado em
`artifacts/audit-post-e13-binary-vector-contour-20260912-r1/`.

## Ajuste controlado no teste

O harness `scripts/capture_e03_asset_library_binary.ps1` recebeu apenas as
capturas de salvar e recarregar (`14-vector-contour-saved.png` e
`15-vector-contour-reloaded.png`). Não houve alteração no código do produto,
schema ou dados do usuário.

## Evidência nativa

Executável:

- `build/post-e13-final-build-20260912/release/post-e13-final-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- versão `0.3.0`, idioma `Português (Brasil)`;
- SHA-256 `0A7E2BFF66F91B365D3D415B732A5C8C33265880E7678533F50E99F5A11F6229`.

Pacote: `artifacts/audit-post-e13-binary-vector-contour-20260912-r2/`.

| Passo | Evidência | SHA-256 | Resultado observado |
|---|---|---|---|
| entrada da ferramenta | `06-vector-contour-initial.png` | `4BA5522B1DCAD05AF571CC52427335CDDCE8343F0CD0C2169B8F150746FCF8C0` | painel localizado `Contorno vetorial`, sem asset selecionado |
| asset selecionado | `08-vector-library-selected.png` | `8ACB151D072BC219289E06189AF9E83EDC0A50B45EB2FC1CADA3583187961261` | `vector-source` selecionado; botões de detecção habilitados |
| detecção | `11-vector-contour-detected.png` | `09EC957CF639473E8980B955D837D6F728804090878339CA0E4ABA2EBADFFE4A` | `Detectado · 4 vértices`, com hash de origem exibido |
| vértice editado | `12-vector-contour-edited.png` | `962D695D9DB9983A5815E81D2CAABEF09B6B29337D878D47782AA3407307E8C5` | X/Y do vértice `0` alterados para `-5,00` |
| objeto criado | `13-vector-contour-created.png` | `0F54D5E267269D07FDA8766A8B2A64B031B80E39844F1D47194CA3A544BD9453` | status localizado `Vector scene object created: vector_vector-source` |
| salvo | `14-vector-contour-saved.png` | `A40965228014EB3C5875CF7B2409DA3968EE757A3D60DA3FB9D0FF5AB3AEC7E` | status `Cenário salvo` |
| recarregado | `15-vector-contour-reloaded.png` | `792244DAA3B09B208FB1900868D6A7A68C9208C77D881D0C631E6750F66360B0` | objeto reaparece no viewport; status `Cenário recarregado` |

Persistência confirmada em
`artifacts/audit-post-e13-binary-vector-contour-20260912-r2/vector-contour-fixture/vector-contour.ndtscene.json`:

- SHA-256 `C14DAE47FE26842E0AD2A17470E7413228AB961FD394F7D5109A07E83C1B8581`;
- `object_count = 1`;
- `vector_geometry` presente;
- `collision_polygon` com 4 vértices;
- origem do asset `4bffd31518cb8eabcfba2b2a4379ba54d6a1632ebd8836b1cbae36f9b33a9a18`.

## Verificação de domínio

Execução focada diagnóstica, separada da suíte oficial:

```text
tests/test_e09_vector_scene_resource.py
tests/test_e09_vector_contour_panel.py
tests/test_e09_vectorization.py
tests/test_e09_contour_editing.py
19 passed in 2.34s
```

## Resultado e limites

- O fluxo técnico de detecção, correção, criação, persistência e reabertura
  passa no binário real e nos contratos E09.
- A ferramenta mostra o estado e a origem hash-bound, sem ocultar erro ou
  fallback.
- Durante a edição o viewport permanece como grade vazia; a captura prova a
  operação pelo painel/status, mas não apresenta o contorno sobre o asset.
  Isso é `UX_REFINEMENT_OPEN`, não falha de persistência.
- Após criação/reload o foco visual vai para `Inspetor > Clipe`, e a seleção
  vetorial não é restaurada no painel da ferramenta. A reabertura do objeto foi
  comprovada, mas a restauração de contexto é `UX_REFINEMENT_OPEN`.
- Este lote não prova consumo do objeto vetorial em runtime Godot/Unity; a
  matriz de engines permanece separada.

## Classificação de governança

`PASS` técnico para a operação nativa e o round-trip do documento; os dois
refinamentos de feedback/contexto permanecem abertos. O lote r1 não foi
apagado nem reclassificado.
