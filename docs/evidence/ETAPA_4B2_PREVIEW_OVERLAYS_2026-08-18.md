# Evidência — Etapa 4B.2: preview no canvas e overlays

## Identificação

- Escopo: preview de cenário somente leitura no canvas, moldura de aspect ratio,
  safe area e máscara de recorte.
- Commit técnico publicado: `638db729ac51988ecce3edb54785aff33bf1687c`.
- Base verificada: `c018a6dcabdc2a0e3f2a90d1fe323618ee706626`.
- Estado: **APROVADO NO ESCOPO 4B.2 / PRÓXIMA ETAPA PENDENTE**.
- O identificador literal da branch não é persistido; o SHA do commit é a âncora
  da proveniência.

## Contrato implementado

O preview é uma camada visual runtime, desativada por padrão, que reutiliza a
imagem iluminada e projeta objetos por `OrthographicCamera` e
`ParallaxLayer`. A camada não altera `Scene`, `SceneObject.polygon`, posição,
seleção, histórico de comandos, schema `.ndtproj` v1, schema lateral v1,
gizmo, exportadores ou integrações de engine.

A interface expõe, no menu Visualizar, duas ações independentes:

- `Scenario Preview (Read-Only)` / `Preview de Cenário (Somente Leitura)`;
- `Safe Frames and Crop Overlay` / `Molduras Seguras e Máscara de Corte`.

A segunda ação fica desabilitada fora do preview. Clique esquerdo, ferramentas,
gizmo e menu de contexto são bloqueados durante o preview; pan de câmera pelo
botão do meio e zoom pelo wheel são operações somente visuais. Ao sair, o modo
normal de edição é restaurado. O adaptador de ações mantém a MainWindow no
limite estrutural de 1.198 linhas.

A geometria de overlay é validada antes do desenho: viewport positivo, aspect
ratio inteiro positivo, safe fraction finita em `(0, 1]`, frame centralizado,
safe area contida no frame e quatro regiões de recorte contidas no viewport.
Redimensionamento do canvas recalcula a geometria real do viewport.

## Testes reais e resultados

Ambiente executado no Windows local com Python 3.11.9, Poetry 2.4.1 e PySide6
6.10.1. Comandos relevantes:

```text
poetry check --lock --strict
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools scripts/audit_scenario_preview.py
poetry run flake8 src tests tools app.py pack_for_ai.py scripts/audit_scenario_preview.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py scripts/audit_scenario_preview.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py scripts/audit_scenario_preview.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest -q tests/test_scenario_preview.py tests/test_stage4b2_preview_overlays.py --tb=short
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools/check_coverage_policy.py coverage.xml
python scripts/audit_scenario_preview.py
```

Resultados observados:

- testes focais do modelo e integração Qt: **13 passed, 0 failed**;
- teste estrutural adicional da refatoração Qt: **35 passed, 0 failed** no
  conjunto combinado com os focais;
- suíte completa: **1.283 passed, 2 skipped, 10 warnings**;
- skips: os dois casos condicionais históricos de symlink da integração; não
  foram criados, removidos ou usados para obter aprovação;
- cobertura XML: `14.275/15.389` linhas (`92,76%`) e `4.230/4.964`
  branches (`85,21%`); cobertura combinada do gate: `90,92%`;
- política de cobertura: aprovada;
- `scenario_preview.py`: 100% de linhas e branches;
- `scenario_preview_actions.py`: 100% de linhas e branches;
- pip-audit: nenhum advisory conhecido; o pacote local não publicado no PyPI
  permanece explicitamente não auditável;
- Bandit: nenhum achado no nível configurado;
- baseline estrutural: MainWindow reduzida de 1.226 linhas durante a primeira
  tentativa para 1.198 linhas após a extração do adaptador; o teste estrutural
  passou sem alteração de limiar.

## Prova de isolamento e não regressão

Os testes Qt criam uma `Scene` real com imagem RGBA, objeto poligonal e
`CommandManager`. Durante o preview, clique esquerdo e pan não alteram:

- polígono do objeto;
- posição do objeto;
- seleção;
- contagem de Undo.

O pan altera somente a câmera runtime. Ao desabilitar o preview, o clique no
objeto volta a selecionar pelo caminho normal. O teste também redimensiona o
canvas de `640x480` para `800x600` e confirma que a geometria do overlay usa o
viewport real.

A captura real da MainWindow em `1280x720` produziu quatro estados. O estado
`normal_after_preview` tem o mesmo SHA-256 de `normal_editing`, demonstrando
retorno byte a byte ao estado visual inicial para o mesmo processo e fixture.

## Auditoria dos PNGs e geometria Qt

O auditor `scripts/audit_scenario_preview.py` leu os PNGs com Pillow e arrays
NumPy, verificou dimensões, modo, alfa, bordas, hashes e cores dos overlays, e
gerou uma anotação com frame e safe area. A geometria foi obtida do widget Qt
real:

- janela capturada: `1280x720`;
- canvas: origem `[158, 55]`, tamanho `[778, 665]`;
- frame 16:9: `[0.0, 113.6875, 778.0, 437.625]` no canvas;
- safe area: `[38.9, 135.56875, 700.2, 393.8625]`;
- pixels ciano detectados: `3166`;
- pixels amarelos detectados: `934`;
- alfa: `[255, 255]` em todos os PNGs;
- dimensões: `[1280, 720]` em todos os PNGs;
- bordas não pretas: `4000` pixels em cada captura, sem transparência ou
  arquivo vazio.

A inspeção visual da captura anotada confirmou que a moldura e a safe area ficam
no canvas, sem sobreposição com os painéis laterais. O estado normal mantém a
área de edição e o gizmo existentes. O renderizador offscreen desta execução
apresentou fallback de glifos quadrados nos textos tanto no estado normal quanto
no preview; isso é uma limitação do ambiente de captura e não foi apresentado
como prova de legibilidade no Windows interativo.

## Falhas de processo encontradas e tratadas

1. Uma primeira medição focada usou alvos `--cov` em formato de caminho `.py` e
   produziu `module-not-imported/no-data-collected`. O resultado foi descartado
   como medição inválida e a cobertura foi repetida com nomes de módulo reais.
2. A primeira suíte completa encontrou uma regressão estrutural real: a
   MainWindow ficou com 1.226 linhas. O gate não foi relaxado; a integração foi
   extraída para `scenario_preview_actions.py`, o teste estrutural foi repetido
   e passou, seguido de uma nova suíte completa com 1.283 testes aprovados.

Nenhuma regra, asserção, skip, xfail ou gate foi alterado para produzir PASS.
Não houve force push, force merge, alteração do schema v1 ou escrita em projeto
externo.

## Limitações e próximo gate

Esta etapa não implementa painel de camadas, inspetor, persistência completa,
Undo/Redo de autoria, exportação do cenário ou validação de consumidores
Godot/Unity. O vínculo runtime de objetos às camadas é uma API interna para a
prova do preview; a autoria persistida será tratada na Etapa 4B.3. Não há
claim de suporte a partículas, shaders, DoF ou runtime completo.

A Etapa 4B geral permanece aberta. O próximo gate é a Etapa 4B.3, que só poderá
começar após a validação documental deste commit técnico e deste conjunto de
artefatos.

## Artefatos hashados

O manifesto em
`docs/evidence/artifacts/stage4b2-preview-2026-08-18/manifest.json` vincula os
arquivos técnicos, testes, script, relatório e PNGs ao commit técnico publicado.
Ele também registra a geometria Qt, invariantes da cena, checagens de pixels,
dimensões, alfa e SHA-256 de cada captura.

## Decisão

**APROVADO NO ESCOPO DA ETAPA 4B.2.** O preview somente leitura e os overlays
estão implementados, integrados ao menu, testados com Qt real, auditados por
PNG/hash e comprovadamente isolados do modo normal. A aprovação não promove a
Etapa 4B geral, não aprova release e não antecipa as etapas 4B.3–4B.5.