# Evidência P2D-05 — crash nativo Qt no Windows

**Data:** 01/09/2026 (UTC-03)
**Status:** BLOQUEADO para encerramento da causa-raiz e merge corretivo
**Repositório:** AiltonSantanaReis/NeoEng-D-Trace
**Branch:** p2d-05-ui-crash-root-cause
**HEAD auditado:** c39fef094669e04a5ad5a365184f61752602ab33
**Base:** main em 0ab59eb40f8c31e482d9cad51543e7fd5e2090d5
**PR corretiva:** https://github.com/AiltonSantanaReis/NeoEng-D-Trace/pull/165

## Objetivo e escopo

Reativar os 11 testes Qt que haviam sido convertidos em skip condicional no
Windows hospedado e investigar o crash nativo que motivou essa alteração. O
escopo desta evidência é a cadeia de testes, o ambiente Windows/offscreen, o
ciclo de vida observado e a decisão de engenharia. Não autoriza alterar
asserções, thresholds, cobertura, workflow obrigatório, produto, exportação,
round-trip ou contratos P2D-05.

## Alterações no branch corretivo

Os commits abaixo somente removem os skips indevidos e mantêm a baseline
coerente com os bytes rastreados:

- 107beff — reativa os 11 casos, sem alterar as asserções;
- 19d62b7 — atualiza hashes/tamanhos da baseline para os três arquivos de
  teste alterados;
- 80cca85 — restaura o import sys necessário pelo fixture existente;
- c39fef0 — preserva o agrupamento de imports exigido pelo isort.

Não houve alteração de produto em src/, de regras do CI, de thresholds, de
skip/xfail ou de cobertura para obter resultado verde.

## Ambiente

### CI histórico com falha

- runner: windows-latest;
- Python: 3.11.9;
- QT_QPA_PLATFORM=offscreen;
- source SHA: 7c866fa60e5e818656c92f55c58b751f0b5408f9;
- workflow run: 33469733446;
- job Windows: 99736873512.

### CI corretivo

- runner: windows-latest;
- Python: 3.11.9;
- QT_QPA_PLATFORM=offscreen;
- source SHA: c39fef094669e04a5ad5a365184f61752602ab33;
- workflow run: 33474669743;
- primeira execução Windows: 99751339437;
- reexecução Windows do mesmo SHA: 99752967164.

### Validação local

- plataforma: win32;
- Python: 3.11.9;
- pytest: 9.1.1;
- PySide6 do lock: 6.10.1;
- CI=true;
- QT_QPA_PLATFORM=offscreen.

## Comandos executados

No branch corretivo, foram executados os gates focais sem modificar os
arquivos durante a execução:

~~~
CI=true QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q \
  tests/test_stage5_viewport_hud.py \
  tests/test_stage5_viewport_hud_contract.py \
  tests/test_stage6_gizmo_gap_closure.py
~~~

Resultado do conjunto focal: 22 passed.

Também foi repetida 25 vezes a sequência que antecedeu o crash histórico,
selecionando os dois casos iniciais de Stage 5, os sete casos ativos de
MaskViewer/X-Ray e o primeiro teste visual de gizmo. Cada processo coletou 10
testes e terminou com 10 passed; resultado agregado: 25/25 iterações passaram.

Os gates remotos foram executados pelo workflow versionado, sem bypass:

~~~
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 \
  --cov-report=term-missing --cov-report=xml
~~~

## Resultados

### Falha histórica observada

No run 33469733446, o job Windows coletou 1857 items. Depois dos testes
ativos de Stage 5, o processo registrou:

~~~
Windows fatal exception: access violation
File tests/test_stage6_gizmo_gap_closure.py, line 43, in
test_vertex_gizmo_exposes_only_xy_handles_and_anchors_selected_vertex
~~~

O log não contém dump nativo, stack de Qt, módulo/DLL responsável ou
diagnóstico de ownership. A linha registrada é o último frame Python exposto,
não uma prova de que aquela linha seja a causa.

### Execuções corretivas

Nos dois jobs Windows do SHA c39fef0 — a execução inicial e a reexecução —
os 11 casos foram executados. A suíte principal terminou com 1858 passed e
1 warning, sem os 11 skips. A cobertura combinada registrada foi 90,87% e
o gate de cobertura passou. O step de reconciliação do legado passou como
reconciliação; isso não significa que todos os testes históricos esperados
foram convertidos em sucesso.

Os jobs Linux correspondentes também passaram. Esses resultados comprovam que
o branch corretivo não mascara os casos e que o crash não foi reproduzido nos
dois runs completos atuais; não comprovam a causa-raiz nem permitem declarar
que o defeito histórico foi corrigido.

## Falhas e causa-raiz

**Causa-raiz:** não determinada.

O fato comprovado é um access violation nativo em um runner Windows hospedado,
após uma sequência de superfícies Qt e no momento em que o primeiro teste
visual de gizmo era iniciado. A mesma sequência passou 25 vezes no Windows
local e a suíte completa passou duas vezes no windows-latest após a
reativação. A divergência impede atribuir causalidade ao gizmo, ao
QApplication, ao QTimer, ao QThreadPool, ao backend offscreen ou ao runner
sem um dump reproduzível.

Há uma hipótese de lifecycle/teardown Qt envolvendo widgets, callbacks
pendentes e recursos nativos, mas ela permanece somente hipótese. Nenhuma
alteração de produto foi feita com base nela.

## Limitações e riscos residuais

- o crash histórico não produziu minidump ou stack nativo;
- a validação local não é o mesmo host/imagem do windows-latest;
- duas execuções verdes atuais reduzem, mas não eliminam, a hipótese de
  intermitência;
- a ausência dos 11 skips é obrigatória, mas não constitui evidência de
  estabilidade causal;
- enquanto a causa não for isolada e corrigida com teste de regressão, a PR
  corretiva não deve ser mesclada.

## Próximos passos obrigatórios

1. manter os 11 casos ativos no gate normal;
2. adicionar coleta diagnóstica de dump nativo somente em caso de falha, sem
   retry e sem alterar o resultado do job;
3. se o crash ocorrer novamente, correlacionar dump, DLL/stack, versão Qt,
   ordem de testes e estado de teardown;
4. somente então aplicar a correção mínima na camada comprovadamente causal e
   adicionar uma regressão positiva/negativa correspondente;
5. repetir todos os gates no SHA exato e revalidar a cadeia de evidências antes
   de qualquer merge.

## Decisão

BLOQUEADO — os testes foram reativados e estão executando sem mascaramento,
mas o crash histórico permanece sem causa-raiz comprovada. Não há base técnica
para afirmar que os problemas foram resolvidos ou para concluir o ciclo de
merge.
