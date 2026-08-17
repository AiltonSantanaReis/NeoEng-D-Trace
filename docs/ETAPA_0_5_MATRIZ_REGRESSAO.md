# Etapa 0.5 — Matriz inicial de regressão

Legenda:

- **Aprovado**: teste executado e aprovado no ambiente indicado;
- **Parcial**: existe evidência, mas a cobertura é insuficiente;
- **Pendente Windows**: requer execução com PySide6/Python 3.11;
- **Incompatível histórico**: teste antigo não corresponde diretamente à API ou
  expectativa atual;
- **Não validado**: implementação encontrada sem teste suficiente.

| Área | Evidência atual | Teste atual | Teste histórico | Estado inicial | Portão antes de refatorar |
|---|---|---|---|---|---|
| Inicialização | Aplicativo abriu no Windows | Manual | Não consolidado | Parcial | Smoke test repetível |
| Cena | Modelo atual e reparo | 3 testes de reparo | Camadas, grupos e comandos | Parcial | Round-trip e invariantes |
| Camadas | Código e painel presentes | Cobertura atual indireta | 2 testes + comandos | Parcial | Restaurar testes de camada |
| Grupos | Código e painel presentes | Cobertura atual indireta | 2 testes | Parcial | Restaurar testes de grupo |
| Undo/redo | CommandManager presente | Física/ferramentas indiretas | Vários testes históricos | Parcial | Matriz execute/undo/redo |
| Detecção automática | 5 testes atuais | Aprovado no Linux | 30 testes históricos aprovados no subconjunto | Parcial | Corpus real no Windows |
| Broadphase SAP | 3 testes atuais | Aprovado no Linux | 14 testes históricos aprovados | Aprovado parcial | Benchmark e casos limite |
| Reparo de polígonos | 3 testes atuais | Aprovado no Linux | Não equivalente | Aprovado parcial | Property tests |
| Física central | 6 testes atuais | Aprovado no Linux | Cobertura histórica adicional | Parcial | Timestep e callbacks |
| SAT | API atual funciona em testes novos | Parcial | 13 testes bloqueados por API | Incompatível histórico | Definir compatibilidade |
| Decomposição convexa | Implementação presente | Teste atual limitado | 1 de 19 falhou | Parcial | Caso côncavo de referência |
| Edge/Sobel | Implementação presente | Sem teste atual específico | 1 de 8 falhou por dtype | Incompatível histórico | Decidir contrato de dtype |
| Curvature simplify | Implementação presente | Sem teste atual específico | 1 de 7 falhou | Parcial | Definir tolerância geométrica |
| Atlas | Exportador presente | Teste atual básico | Rotação divergiu para resultado melhor | Incompatível histórico | Golden files |
| Sprite | Exportador presente | Teste atual básico | Históricos majoritariamente aprovados | Parcial | Transparência e limites |
| JSON genérico | Exportador presente | Teste atual básico | Históricos majoritariamente aprovados | Parcial | Schema versionado |
| Godot | Perfil presente | Sem validação na engine | Metadado histórico divergente | Não validado | Abrir pacote no Godot |
| Unity | Perfil presente | Sem validação na engine | Metadado histórico divergente | Não validado | Importador e teste Unity |
| Phaser | Perfil presente | Sem validação na engine | Metadado histórico divergente | Não validado | Fixture Phaser |
| GLTF/GLB | Exportador novo | Teste atual depende de biblioteca | Sem teste histórico | Parcial | Validar GLB externo |
| Caneta | Ferramenta presente | Teste novo exige Qt | 19 testes históricos pendentes | Pendente Windows | Executar eventos reais |
| Laço livre | Duas implementações | Teste novo exige Qt | 7 históricos pendentes | Pendente Windows | Comparação A/B |
| Laço magnético | Ferramenta presente | Teste novo exige Qt | 15 históricos pendentes | Pendente Windows | Imagens e eventos reais |
| Laço poligonal | Ferramenta presente | Teste novo exige Qt | 10 históricos pendentes | Pendente Windows | Eventos e cancelamento |
| Retângulo/elipse | Ferramentas presentes | Testes novos exigem Qt | 14 históricos pendentes | Pendente Windows | Seleção e contexto |
| Edição de polígonos | Ferramenta nova | Teste novo exige Qt | Sem equivalente completo | Pendente Windows | Vertex/edge/undo |
| Pincel de colisão | Ferramenta nova | Sem cobertura suficiente | Sem equivalente | Não validado | Escala, mover e cancelar |
| Mask Viewer | Interface presente | 1 teste atual Qt | 9 históricos pendentes | Pendente Windows | Worker, zoom, pan, seleção |
| Canvas/modos | Interface presente | 3 testes atuais Qt | Cobertura histórica indireta | Pendente Windows | Mouse, zoom e ferramentas |
| Persistência | JSON presente | Sem round-trip completo | Cobertura insuficiente | Não validado | Schema e migração |
| Configuração | ConfigManager presente | Sem suíte dedicada atual | Cobertura indireta | Parcial | Corrupção e gravação atômica |
| Empacotamento Windows | Não entregue | Nenhum | Nenhum | Não validado | Build reproduzível |

## Atualização operacional — Etapa 10 dos adaptadores nativos

O quadro acima é o inventário inicial e permanece preservado. O estado operacional atual da integração de engines é:

| Área | Evidência executada | Estado atual | Gate restante |
|---|---|---|---|
| Godot source-only | Fixture real, importação, dry-run, aplicação, repetição, conflito manual, drift de hash e regressão da Etapa 4 | Aprovado tecnicamente no commit `a713b8d9a28818bae2c72a2fab35e79f2f4e157d` | CI pré e pós-merge PASS; engines reais permanecem evidência local |
| Unity source-only | Fixture real, importação, dry-run, aplicação, repetição, conflito manual, drift de hash e regressão da Etapa 6 | Aprovado tecnicamente no commit `a713b8d9a28818bae2c72a2fab35e79f2f4e157d` | CI pré e pós-merge PASS; engines reais permanecem evidência local |
| Determinismo | Projetos independentes e normalização apenas de identificadores internos não semânticos | Aprovado tecnicamente no commit `a713b8d9a28818bae2c72a2fab35e79f2f4e157d` | Integridade pós-commit confirmada |
| Evidências | Índice SHA-256, reabertura dos artefatos, privacidade e falhas intermediárias registradas | Aprovado tecnicamente no commit `a713b8d9a28818bae2c72a2fab35e79f2f4e157d` | Auditoria remota concluída na PR #84 |

Referência: `docs/evidence/ETAPA_10_ADAPTADORES_NATIVOS_ENCERRAMENTO_2026-08-17.md`.

## Regra de liberação

Uma linha não pode passar para “Aprovado” por revisão visual do código. Deve haver:

1. teste executado;
2. ambiente registrado;
3. entrada de referência;
4. saída esperada;
5. evidência armazenada;
6. rollback definido.
