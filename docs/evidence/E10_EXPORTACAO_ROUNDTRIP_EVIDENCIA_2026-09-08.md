# E10 — exportação real e round-trip Godot/Unity

**Data de abertura:** 2026-09-08  
**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Plano Mestre:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Status:** `IN_PROGRESS`

## Contrato de execução

E10 implementa e comprova `EXP-001/002/003/004/005`, integrando os recursos
qualificados em E01–E09. O aceite distingue explicitamente:

1. save/reopen interno do documento;
2. exportação para um pacote validado;
3. importação em projeto limpo da engine;
4. execução real e comparação visual/funcional;
5. retorno à autoria, somente se houver importador reverso e política de
   identidade/conflito implementados.

JSON/sidecar isolado não será tratado como execução real. Cada destino terá
versão detectada, capacidades suportadas, diferenças aceitáveis, negativos,
logs e capturas nativas.

## Inventário inicial verificável

- Godot foi localizado no host como `C:\ProgramData\chocolatey\bin\godot.exe`;
  a versão e a execução headless serão registradas no primeiro sublote.
- Nenhum executável Unity foi localizado pelos comandos de descoberta do host;
  a integração Unity permanece uma lacuna de disponibilidade externa até que
  um runtime qualificável seja encontrado, sem converter scaffold C# em prova
  de engine real.
- O repositório já contém adapters, validadores e plugins Godot/Unity; eles
  serão usados como implementação candidata e não como evidência de consumo
  até a execução correspondente.

## Fila E10

| Sublote | Status | Saída obrigatória |
|---|---|---|
| E10-A contrato/capacidades | `IN_PROGRESS` | matriz por destino e versão, propriedades preservadas, conversões e limites |
| E10-B exportação efetiva | `PLANNED` | pacote temporário validado, hash, atomicidade e negativos |
| E10-C importação/execução Godot | `PLANNED` | projeto limpo, importador real, runtime, logs e capturas |
| E10-D importação/execução Unity | `PLANNED` | runtime Unity real, ou lacuna de disponibilidade explicitamente mantida |
| E10-E round-trip/fechamento | `PLANNED` | comparação visual/funcional, retorno somente se implementado, suíte e manifesto |

## Regras de evidência

- Não declarar round-trip visual completo com base somente em JSON.
- Usar fixtures assimétricas para revelar inversão de eixo, escala, pivô e
  rotação.
- Preservar saída válida anterior durante exportação interrompida ou inválida.
- Manter symlink e revisão humana exclusivamente na auditoria final.

Este documento será atualizado somente com comandos, versões, hashes, logs,
capturas e limitações reproduzíveis.
