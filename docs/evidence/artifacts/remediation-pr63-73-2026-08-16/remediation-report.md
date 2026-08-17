# Evidência — Remediação PRs #63–#73

## Identificação

- Escopo: remediação no estado atual baseado em origin/main; as PRs históricas #63–#73 não foram reescritas.
- HEAD/base: d617f3b50aa73c3e10a85ff740dc0ebe3a887731
- Branch: remediation-pr63-73
- Data/hora UTC: 2026-08-17T00:10:15.2450437Z
- Estado: commit local criado; nenhum push/merge executado nesta etapa.

## Objetivo e escopo

Reproduzir defeitos associados às PRs #63–#73, corrigir somente falhas comprovadas e validar detecção automática, limites, UI, exportação/transação e integrações reais Godot/Unity.

## Ambiente

- Sistema: Windows
- Python: 3.11.9
- Godot: 4.7.stable.official
- Unity: 6000.5.7f1
- Qt: PySide6 offscreen para a captura UI
- CuPy ausente; o projeto registrou fallback explícito para CPU.

## Falha reproduzida e correção

Antes da correção, o corpus ring_hole/basic registrou IoU=0.829384, boundary F1=0.832593 e furos=0/1.

A causa foi cv2.RETR_EXTERNAL no modo básico, que descartava a hierarquia interna. A correção adiciona detect_holes com padrão verdadeiro, usa cv2.RETR_CCOMP quando habilitado e preserva furos no campo holes do objeto externo. detect_holes=False continua disponível como caminho explícito. Foi adicionado teste de regressão no corpus ring_hole.

Após a correção, o mesmo caso registrou IoU=0.977843, boundary F1=1 e furos=1/1.

## Comandos e resultados

- Testes direcionados: 103 passed.
- Suíte completa: 1122 testes; falhas=0; erros=0; skips=0; 10 avisos de depreciação Qt.
- Benchmark automático: 44 execuções; erros=0; não determinismos=0; quality gate: PASS; nenhum caso abaixo de IoU 0.94, boundary F1 0.95, contagem esperada ou determinismo.
- Limite de 2.000 pontos: casos negativos cobertos pela suíte; corpus real de alta densidade dentro do limite após simplificação.
- UI: três resoluções com tamanhos capturados iguais aos solicitados; estados sem projeto, projeto/painéis, gizmo, validação e modal gerados com hashes.
- Godot Stage 3 ZIP=SUCCESS; Stage 4=SUCCESS; Stage 7=SUCCESS.
- Unity Stage 5=SUCCESS; Stage 6=SUCCESS; Stage 7=SUCCESS.

## Incidentes de execução

Duas primeiras chamadas Unity foram inválidas por erro de invocação do agente: caminho do Python confundido com saída e função interna incorreta. Nenhuma executou o auditor ou gerou relatório de produto. As chamadas corrigidas foram repetidas em diretórios novos e passaram; os incidentes permanecem registrados.

## Artefatos

- auto-detection-after-fix/report.json
- ui-after-fix/manifest.json e PNGs das três resoluções
- relatórios Godot Stages 3, 4 e 7
- relatórios Unity Stages 5, 6 e 7
- full-suite-after-fix-sanitized.xml (comparativo anterior)
- full-suite-final-sanitized.xml (execução final após a correção UI)
- ui-final/manifest.json e PNGs das três resoluções
- manifest.json com hashes byte a byte

## Limitações e riscos residuais

- A inspeção visual pixel-a-pixel pelo visualizador integrado foi bloqueada pelo ACL do executor (apply deny-read ACLs). Não é permitido declarar ausência de clipping, sobreposição ou inconsistência cromática apenas a partir dos PNGs; dimensões e hashes foram validados.
- CuPy não está instalado; não há evidência de desempenho GPU nesta execução.
- O corpus é sintético/adversarial e não prova perfeição para toda imagem real.
- Os 10 avisos Qt são depreciações conhecidas e permanecem registrados.
- Não há base honesta para afirmar que todas as limitações históricas das PRs foram eliminadas universalmente.

## Decisão

PARCIAL — a falha comprovada do modo básico foi corrigida e os gates automatizados e de engine executados passaram. A auditoria visual completa permanece bloqueada; não declarar encerramento total das PRs #63–#73 nem aprovação de push/merge com base somente neste pacote.