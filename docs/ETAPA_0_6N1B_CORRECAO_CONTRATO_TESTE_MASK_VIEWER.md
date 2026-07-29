# Etapa 0.6N1B — correção do contrato de teste do Mask Viewer

## Diagnóstico confirmado

A Etapa 0.6N1A foi aplicada corretamente. No Windows, 113 de 114 testes da suíte oficial passaram. A única falha foi uma asserção textual do teste `test_mask_viewer_is_bilingual_and_language_change_preserves_view`.

O runtime preservou o título histórico em inglês:

- `Mask Viewer - Auto Detection X-Ray`

E forneceu a tradução correspondente em português:

- `Visualizador de Máscara - Raio-X de Detecção Automática`

O teste novo esperava, incorretamente, títulos abreviados que removiam a informação `X-Ray`/`Raio-X`. O problema estava no contrato do teste, não no código de runtime.

## Alteração

Somente as duas expectativas de título em `tests/test_stage_0_6n1a_runtime_ui.py` foram alinhadas ao comportamento histórico preservado e à tradução implementada.

Nenhum arquivo de `src/` foi alterado. Não houve mudança de algoritmo, interface, exportação, formato, configuração, Git ou dados do usuário.

## Portões obrigatórios

- compilação sintática;
- teste Qt 0.6N1A completo;
- teste do motor de preview;
- testes de identidade;
- checkpoint 0.5.2F3;
- suíte oficial completa;
- auditoria de privacidade e mistura de projetos;
- validação visual ainda obrigatória para responsividade, traduções e dimensionamento da paleta.
