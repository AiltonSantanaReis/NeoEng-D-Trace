# Etapa 0.5.2 — Resultados reais dos testes históricos no Windows

Data: 27 de julho de 2026.

## Ambiente

- Windows 10 build 26200;
- Python 3.11.9;
- integridade dos snapshots históricos: aprovada;
- commit de origem: `cf749564ab5d961772d66dc363d0e990cebf8da3`.

## Totais

Foram executados 184 testes históricos:

- 161 aprovados;
- 22 falharam;
- 1 erro de coleta;
- nenhum teste ignorado.

Grupo não gráfico:

- 101 testes reportados;
- 92 aprovações;
- 8 falhas;
- 1 erro de coleta.

Grupo Qt:

- 83 testes;
- 69 aprovações;
- 14 falhas.

## Regressões confirmadas e corrigidas nesta subetapa

### Perfis de exportação

`export_metadata()` deixou de chamar os formatadores já existentes para Godot,
Unity e Phaser. O caminho principal devolvia metadados genéricos e tornava os
módulos específicos inacessíveis.

Correção: despacho explícito e restrito aos três perfis suportados. O formato
genérico atual foi preservado.

### API pública SAT

As funções históricas `project()` e `polygon_edges()` deixaram de ser
exportadas, impedindo a coleta de 13 testes. A política histórica para geometria
incompleta também era retornar `(False, None)`, enquanto a implementação atual
levantava `ValueError`.

Correção: wrappers compatíveis e retorno não colidente para polígonos com menos
de três vértices. O cálculo SAT/MTV para polígonos válidos não mudou.

### Transformação do MaskViewer

`get_view_transform()` e `set_view_transform()` desapareceram, e
`image_to_view()` deixou de aceitar tuplas.

Correção: API aditiva restaurada. O comportamento atual de `reset_view()`, que
preenche a área disponível, foi mantido porque existe teste atual explícito
para esse contrato.

## Casos classificados sem correção funcional

- rotação do atlas: melhoria atual; o teste antigo esperava a ausência do recurso;
- `float32` no Sobel: contrato de precisão ainda precisa de benchmark;
- decomposição convexa: fixture histórica precisa de validação geométrica;
- comando de alças: fixture usa polígono colinear rejeitado corretamente;
- simplificação de círculo: precisa de métrica de erro, não somente contagem;
- PenTool e MagneticLasso: falhas produzidas por mocks sem retorno numérico em
  `get_zoom()`;
- overlay do laço poligonal: mock de conversão incompatível com a API atual;
- testes integrados do retângulo: fixture usa `Mock` como modelo, tornando
  `hasattr(model, "cmd")` verdadeiro de forma artificial.

## Pendências reais

O duplo clique do laço poligonal apresenta divergência de estado e será validado
com teste de interação real antes de qualquer alteração.

A decomposição convexa e a simplificação por curvatura exigem corpus geométrico
e métricas antes de uma decisão.

## Regra de não regressão

Nenhum snapshot histórico foi editado. As correções foram protegidas por novos
testes ativos e não removem APIs atuais.
