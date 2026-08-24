# Adendo Normativo — Automação de Evidências e Identificadores Estáveis

**Versão:** 1.0  
**Data:** 2026-08-24  
**Aplicação:** obrigatória antes do início da Fase 4 do plano profissional

## 1. Objetivo

Este adendo torna obrigatória a automação da coleta, validação e empacotamento de evidências antes da construção do `SceneViewport` profissional.

O objetivo é evitar que a governança seja executada manualmente, tardiamente ou de forma inconsistente. A automação deverá estar pronta quando a Fase 4 começar, e não depois que os recursos críticos já tiverem sido implementados.

Este adendo complementa o plano normativo completo. Em caso de conflito, este adendo prevalece para:

- identificação de módulos, requisitos, features, componentes, testes, evidências, builds e baselines;
- automação de rastreabilidade;
- coleta e validação de pacotes de evidência;
- gate de entrada da Fase 4.

O registro canônico dos IDs está em:

[REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml](C:/Users/atnco/Pictures/NeoEng-D-Trace/docs/REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml)

## 2. Taxonomia obrigatória de IDs

Todos os IDs deverão ser únicos, estáveis, sem acentos, em maiúsculas, separados por hífen e imutáveis depois de publicados.

### 2.1 Formatos

| Categoria | Formato obrigatório | Exemplo |
|---|---|---|
| Módulo | `MOD-[CAMADA]-[NOME]` | `MOD-RENDER-CORE` |
| Requisito | `REQ-F[FASE]-[DOMINIO]-[NOME]` | `REQ-F07-LIGHT-DIR` |
| Feature | `FEAT-[DOMINIO]-[ACAO]` | `FEAT-CAM-ORTHO-ZOOM` |
| Componente | `CMP-[TIPO]` | `CMP-POINT-LIGHT` |
| Teste | `TEST-[DOMINIO]-[COMPORTAMENTO]` | `TEST-LIGHT-DIRECTIONAL-PIXELS` |
| Evidência | `EVID-F[FASE]-[TIPO]-[NOME]` | `EVID-F07-GOLDEN-LIGHT-DIR` |
| Build | `BUILD-F[FASE]-[FINALIDADE]-[DATA]-[SHA]` | `BUILD-F04-AUDIT-20260824-98FFBA1` |
| Baseline | `BASE-F[FASE]-[DATA]-[SHA]` | `BASE-F04-20260824-98FFBA1` |
| Decisão | `ADR-[DOMINIO]-[DECISAO]` | `ADR-RENDER-BACKEND` |
| Risco | `RISK-[DOMINIO]-[NOME]` | `RISK-RENDER-GPU-FALLBACK` |

O formato canônico é o único formato válido. IDs livres, nomes de tela, nomes de classe, números sequenciais puros e traduções não poderão substituir os IDs.

### 2.2 Regras de estabilidade

1. Um ID publicado nunca será reutilizado.
2. Renomear uma classe, função, widget, menu ou texto de UI não altera o ID.
3. Um ID descontinuado permanecerá reservado e marcado como `deprecated`.
4. Um requisito dividido em dois receberá dois novos IDs, mantendo o original como histórico.
5. Dois requisitos consolidados receberão um novo ID de destino e manterão os IDs anteriores como aliases históricos.
6. Alteração de texto não é alteração de identidade.
7. Alteração de comportamento exige novo versionamento e atualização da rastreabilidade.
8. O CI deverá rejeitar IDs duplicados, ausentes, inválidos ou reutilizados.

## 3. Automação obrigatória de evidências

### 3.1 Gate de entrada da Fase 4

A Fase 4 NÃO poderá começar enquanto todos os requisitos abaixo não estiverem aprovados:

- `REQ-F02-EVIDENCE-AUTOMATION` implementado;
- `REQ-F01-GOV-ID-REGISTRY` implementado;
- `REQ-F01-GOV-TRACEABILITY` implementado;
- pipeline executada em Windows e Linux;
- pacote de evidência gerado automaticamente;
- manifesto validado;
- hashes validados;
- commit da execução validado;
- matriz requisito–teste–evidência validada;
- falha deliberada do pacote detectada pelo CI;
- relatório de fallback gerado sem intervenção manual.

Esse gate é obrigatório. A existência de testes manuais ou de scripts parciais não autoriza iniciar a Fase 4.

### 3.2 Conteúdo mínimo do pacote

O pipeline deverá criar automaticamente um diretório isolado neste formato:

```text
artifacts/evidence/
  F04/
    BUILD-F04-AUDIT-YYYYMMDD-SHA/
      manifest.json
      traceability.json
      environment.json
      dependency-lock.json
      test-results-junit.xml
      coverage.json
      fallback-report.json
      performance.json
      visual/
      logs/
      hashes.sha256
      package-report.json
```

O pacote deverá conter, no mínimo:

- commit completo;
- branch;
- data e hora UTC;
- sistema operacional;
- versão do Python e dependências;
- versão do schema;
- backend utilizado;
- GPU detectada;
- fallback utilizado;
- resultados JUnit;
- cobertura, quando aplicável;
- métricas de tempo de frame;
- p50, p95, p99 e pior amostra;
- memória inicial e final;
- capturas visuais;
- hash de cada captura;
- matriz de rastreabilidade;
- status final `PASS` ou `FAIL`.

### 3.3 Comportamento obrigatório do pipeline

O pipeline deverá:

1. limpar ou criar um diretório exclusivo da execução;
2. registrar o commit real em execução;
3. carregar o registro canônico de IDs;
4. executar os testes identificados;
5. coletar logs sem truncamento silencioso;
6. coletar capturas visuais;
7. coletar métricas;
8. registrar fallback;
9. gerar manifesto;
10. calcular hashes;
11. validar a matriz de rastreabilidade;
12. confirmar que cada requisito possui teste e evidência exigidos;
13. confirmar que cada teste está associado a um requisito válido;
14. confirmar que cada evidência pertence ao commit executado;
15. falhar quando qualquer item estiver ausente;
16. publicar o pacote apenas após a validação completa.

Nenhuma etapa de copiar, renomear, hashizar ou associar evidência poderá depender de edição manual para uma execução oficial.

### 3.4 Regras específicas para métricas

Métricas de p95 só serão aceitas quando:

- houver quantidade mínima de amostras definida pelo teste;
- o período de aquecimento estiver separado;
- as amostras forem identificadas;
- a unidade estiver registrada;
- o backend estiver registrado;
- o hardware estiver registrado;
- outliers não forem removidos sem justificativa;
- p50, p95, p99 e pior amostra estiverem presentes.

Se a quantidade mínima não for atingida, o resultado será `INSUFFICIENT_DATA`, nunca `PASS`.

## 4. Matriz automática de rastreabilidade

Cada requisito deverá possuir uma entrada semelhante a:

```json
{
  "requirement_id": "REQ-F07-LIGHT-DIR",
  "feature_ids": ["FEAT-LIGHT-DIRECTIONAL"],
  "component_ids": ["CMP-LIGHT-DIRECTIONAL"],
  "test_ids": [
    "TEST-LIGHT-DIRECTIONAL-PIXELS",
    "TEST-LIGHT-DIRECTIONAL-PERSISTENCE",
    "TEST-LIGHT-DIRECTIONAL-RUNTIME"
  ],
  "evidence_ids": [
    "EVID-F07-GOLDEN-LIGHT-DIR",
    "EVID-F07-RUNTIME-LIGHT-DIR"
  ],
  "status": "PENDING"
}
```

O status só poderá ser `PASS` quando todos os testes e evidências obrigatórios estiverem associados ao mesmo commit auditado.

Estados permitidos:

- `PLANNED`;
- `IN_PROGRESS`;
- `BLOCKED`;
- `PASS`;
- `FAIL`;
- `DEPRECATED`.

Não serão aceitos estados livres como “quase pronto”, “funcional”, “validado manualmente” ou “aparentemente correto”.

## 5. Primeiros IDs obrigatórios

O registro inicial deverá incluir, no mínimo:

- `MOD-DOMAIN-SCENE`;
- `MOD-RENDER-CORE`;
- `MOD-RENDER-BACKEND`;
- `MOD-EDITOR-SCENE-VIEWPORT`;
- `MOD-EDITOR-CANVAS-VIEW`;
- `MOD-EDITOR-INSPECTOR`;
- `MOD-EDITOR-LAYER-STACK`;
- `MOD-RUNTIME-PLAYBACK`;
- `MOD-TOOLS-EVIDENCE`;
- `REQ-F01-GOV-ID-REGISTRY`;
- `REQ-F01-GOV-TRACEABILITY`;
- `REQ-F02-RENDER-VERTICAL-SLICE`;
- `REQ-F02-EVIDENCE-AUTOMATION`;
- `REQ-F04-SCENE-VIEWPORT`;
- `REQ-F05-PRO-INSPECTOR`;
- `REQ-F06-2P5D-CAMERA`;
- `REQ-F06-2P5D-PARALLAX`;
- `REQ-F07-LIGHT-AMBIENT`;
- `REQ-F07-LIGHT-DIR`;
- `REQ-F07-LIGHT-POINT`;
- `REQ-F08-PARTICLE-RENDER`;
- `REQ-F08-PARTICLE-REPLAY`;
- `REQ-F09-PLAYBACK-CONTROL`;
- `REQ-F09-RUNTIME-EQUIVALENCE`;
- `CMP-CAMERA-ORTHOGRAPHIC`;
- `CMP-PARALLAX-LAYER`;
- `CMP-LIGHT-DIRECTIONAL`;
- `CMP-LIGHT-POINT`;
- `CMP-PARTICLE-EMITTER`;
- `FEAT-CAM-ORTHO-ZOOM`;
- `FEAT-CAM-DEPTH-PARALLAX`;
- `FEAT-LIGHT-DIRECTIONAL`;
- `FEAT-LIGHT-POINT`;
- `FEAT-PARTICLE-EMIT`;
- `FEAT-PARTICLE-REPLAY`;
- `FEAT-INSP-TRANSFORM`.

## 6. Critérios de aceite da automação

A automação estará concluída somente quando uma execução limpa produzir um pacote completo e quando cinco falhas deliberadas forem detectadas:

1. requisito sem teste;
2. teste sem requisito;
3. evidência sem hash;
4. evidência de commit diferente;
5. fallback omitido.

Cada falha deverá fazer o pipeline terminar com código diferente de zero e gerar diagnóstico explícito.

Também deverá existir uma execução positiva que gere `PASS` com manifesto, rastreabilidade, hashes, logs, JUnit, métricas e relatório de fallback.

## 7. Regra operacional

O trabalho da Fase 4 será bloqueado até o gate de evidências passar em ambos os sistemas operacionais suportados. A automação não poderá ser adiada para o fim do projeto porque os artefatos precisam acompanhar a implementação desde a primeira funcionalidade do renderer.

O objetivo não é criar burocracia manual. O objetivo é que a governança seja executada automaticamente, com falha rápida, rastreabilidade objetiva e baixo custo operacional.
