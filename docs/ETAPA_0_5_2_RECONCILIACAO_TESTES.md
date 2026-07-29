# Etapa 0.5.2 — Reconciliação e preservação dos testes históricos

Data: 27 de julho de 2026.

## 1. Escopo executado

Foram restaurados, sem alteração de conteúdo, os 24 arquivos de teste presentes no
commit `cf749564ab5d961772d66dc363d0e990cebf8da3`. Eles foram colocados em `quality/legacy_tests/tests/`, fora
da coleta oficial definida pelo `pytest.ini` principal.

Total preservado:

- 24 arquivos;
- 196 testes detectáveis;
- 113 testes não gráficos;
- 83 testes dependentes de Qt/PySide6.

Nenhum teste ativo foi removido, renomeado ou modificado nesta entrega.

## 2. Proteções implementadas

- manifesto com commit, blob Git, SHA-256 normalizado, grupo e nomes dos testes;
- validação de integridade antes da execução;
- execução de cada arquivo em subprocesso isolado;
- relatórios JUnit, logs individuais e resumo JSON;
- grupo `non-qt`, grupo `qt` e execução total;
- wrapper PowerShell que usa a `.venv` do projeto;
- saída padrão fora do repositório, em diretório temporário.

Um erro de importação em um arquivo não interrompe nem mascara os resultados dos
outros arquivos.

## 3. Resultado reproduzido no ambiente de auditoria

Ambiente:

- Linux;
- Python 3.13.5;
- PySide6 indisponível.

Resultado dos 113 testes não gráficos:

- 92 aprovados;
- 8 falharam;
- 13 ficaram bloqueados durante a coleta por incompatibilidade na API SAT.

Os 83 testes Qt permanecem pendentes de execução oficial no Windows com Python
3.11.9 e PySide6 6.10.1.

## 4. Classificação das oito falhas

### 4.1 Decomposição convexa

A expectativa antiga exigia cinco partes para uma forma em L. A fixture histórica
possui auto-interseção no anel e é geometricamente inválida. A falha não pode ser
classificada como regressão até o teste ser refeito com uma forma côncava válida.

### 4.2 Sobel `float32` versus `float64`

A implementação atual retorna `float32`, enquanto o teste antigo exigia `float64`.
Isso é mudança de contrato e pode ser otimização válida. Precisão, memória e API
devem ser medidas antes da decisão.

### 4.3 Rotação do atlas

O teste histórico esperava dois atlas porque a rotação ainda não funcionava. A
implementação atual gera um atlas. Isso é uma melhoria provável; o teste antigo
deve ser substituído por uma verificação de ausência de sobreposição, orientação
e metadado de rotação.

### 4.4 Perfis Godot, Unity e Phaser

Três testes confirmaram que `export_metadata(profile=...)` não entrega mais a
estrutura específica da engine. Os módulos de perfil continuam presentes, mas o
exportador atual deixou de despachá-los e passou a aplicar transformação genérica
inline.

Classificação: **regressão funcional confirmada no ambiente de auditoria**.

A correção não foi aplicada nesta entrega. Antes dela serão adicionados testes de
contrato para os três formatos e golden files mínimos.

### 4.5 Comando de alças

A fixture antiga cria três pontos colineares, hoje rejeitados como polígono
inválido. O comportamento de validação atual é defensável. O teste deve usar uma
geometria válida e continuar verificando `execute`, `undo` e `redo`.

### 4.6 Simplificação por curvatura

A simplificação do círculo manteve quatro pontos, enquanto o limite histórico era
oito. É necessário definir uma métrica de erro geométrico; contar pontos isoladamente
não é suficiente para decidir regressão.

## 5. Incompatibilidade SAT

O teste histórico importa `project` e `polygon_edges`. A API atual expõe
`project_polygon` e não expõe `polygon_edges`. Além disso, a implementação atual
lança `ValueError` para polígonos com menos de três vértices, enquanto o contrato
antigo retornava `(False, None)` para polígonos vazios.

Nenhum alias foi criado nesta entrega porque isso mudaria a API pública antes de
serem analisados os chamadores reais. A decisão deverá separar:

- compatibilidade nominal de imports;
- ordem de argumentos da projeção;
- comportamento de polígonos vazios e degenerados;
- política de exceções.

## 6. Relação com a suíte atual

Os testes atuais cobrem parte dos fluxos, mas não substituem integralmente os 196
casos históricos. Os maiores vazios são:

- laço magnético;
- laço poligonal;
- overlays de ferramentas;
- sinais, zoom e pan do Mask Viewer;
- comandos de camadas, grupos e alças;
- suavização;
- edge utilities;
- schemas específicos de exportação;
- casos extremos de detecção automática;
- API SAT histórica.

O arquivo `docs/ETAPA_0_5_2_MAPEAMENTO_TESTES.csv` registra a situação de cada
arquivo histórico e sua cobertura atual relacionada.

## 7. Decisões desta entrega

- preservar todos os testes históricos integralmente;
- não restaurá-los diretamente em `tests/`;
- não alterar código funcional para forçar aprovação;
- não editar expectativas antigas sem registrar a justificativa;
- executar os testes Qt no Windows antes do baseline;
- corrigir regressões confirmadas somente com contrato protegido;
- manter o `pytest` oficial limitado a `tests/`.

## 8. Portões para concluir a Etapa 0.5.2

A fase somente poderá ser encerrada depois de:

1. executar o grupo Qt no Windows;
2. enviar o `summary.json` e os logs produzidos;
3. classificar os 83 testes Qt;
4. criar testes de contrato para Godot, Unity e Phaser;
5. decidir a API SAT;
6. promover os testes históricos ainda relevantes;
7. relacionar cada teste aposentado ao seu substituto.
