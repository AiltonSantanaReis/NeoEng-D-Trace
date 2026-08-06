# Plano de renomeação segura — PolygonTool para NeoEng-D-Trace

**Status:** identidade aplicada; consolidação em árvore única aprovada.
**Data da decisão:** 27 de julho de 2026.

> **Nota de continuidade:** a decisão de árvore única permanece vigente. A seção de preparação Git registra o contexto anterior ao baseline privado e não descreve o estado atual do remote ou das PRs.

## 1. Decisão

- nome de exibição e distribuição: `NeoEng-D-Trace` / `neoeng-d-trace`;
- código-fonte canônico: somente `src/`;
- entrada de desenvolvimento: `app.py`;
- entrada de console: `neoeng-d-trace = src.launcher:main`;
- executável futuro: `NeoEng-D-Trace.exe`;
- configuração legada permanece temporariamente em `<raiz>/config.json`;
- não haverá pacote duplicado, aliases entre árvores ou migração física para `neoeng_d_trace/`.

`APP_ID = neoeng_d_trace` permanece apenas como identificador estável do produto. Ele não representa um namespace importável.

## 2. Regra principal

A mudança de marca preserva o projeto e as melhorias já validadas. Não autoriza reescrita arquitetural, duplicação de módulos ou alteração silenciosa de comportamento.

A renomeação deve alcançar UI, traduções, logger, metadados, GLTF generator, documentação ativa, distribuição, futuro executável e instalador. Referências a PolygonTool podem permanecer apenas em histórico ou compatibilidade de dados explicitamente documentada.

## 3. Estrutura aprovada

```text
app.py
src/
├── collision/
├── core/
├── exporters/
├── models/
├── physics/
├── tools/
├── ui/
└── utils/
```

Não fazem parte da arquitetura aprovada:

- `neoeng_d_trace/` como segunda árvore;
- wrappers que redirecionam `src.*` para outro pacote;
- duas implementações do mesmo módulo;
- `python -m neoeng_d_trace`;
- migração física futura motivada apenas pela marca.

## 4. Identidade central

`src/core/app_identity.py` é a fonte única para nome, versão, logger e generator GLTF. O formato de projeto não será vinculado à marca visual.

## 5. Configuração

A consolidação restaura e preserva a leitura de `<raiz>/config.json`. Uma eventual mudança para `%LOCALAPPDATA%/NeoEng-D-Trace/` será uma melhoria independente, com importação explícita e rollback; não faz parte da troca de nome.

## 6. Testes obrigatórios

- `app.py` abre e apresenta NeoEng-D-Trace;
- entrada de console resolve `src.launcher:main`;
- nenhuma importação de runtime referencia `neoeng_d_trace`;
- não existe segunda árvore de código;
- configuração legada continua na raiz;
- projetos antigos abrem;
- PNG, sprite, atlas, JSON e GLTF/GLB permanecem funcionais;
- GLB preserva generator, geometria, índices, metadados, atomicidade e padding;
- interface permanece disponível em inglês e português;
- rollback restaura o estado anterior.

## 7. Git

Nenhum stage, commit, tag, remote ou push integra a consolidação. O histórico local antigo não será publicado. O baseline privado será uma decisão posterior, depois da validação final no Windows.

## 8. Critério de conclusão

A renomeação estará concluída quando a árvore única `src/` estiver validada, as superfícies ativas exibirem NeoEng-D-Trace, os formatos existentes permanecerem compatíveis e as referências antigas estiverem restritas ao histórico aprovado.
