# Gates finais locais — candidata `6ede2f6` — 04/09/2026

## Identidade e decisão

- Produto auditado: `6ede2f6073f6d2aaf5a394e4043019a3ac85a5e4`.
- Branch: `Ailton/legacy26-closure-audit`.
- C12: `PASS` no escopo local comprovado.
- C13: `PENDING_REMOTE_CI`; push e PR sem merge são os próximos passos, e os
  jobs remotos devem ser analisados antes de qualquer merge.

A revisão visual humana dos seis estados da Caneta foi confirmada pelo
proprietário. Nenhum snapshot legado, manifesto histórico ou artefato local
preexistente foi reescrito.

## Resultado dos gates

| Gate | Resultado objetivo |
| --- | --- |
| Auditoria visual Qt real | `4/4` checks automatizados `PASS`; seis capturas; revisão humana `PASS`; pacote `12/12` íntegro |
| Suíte completa | `1922 passed, 2 skipped, 1 warning` |
| Runner Windows com cobertura | `190/190` arquivos; `1924` testes; `0` falhas; `0` erros; `2` skips; `ACCEPTED` |
| Cobertura integrada | `92,67%` linhas (`23965/25860`) e `85,15%` branches (`6689/7856`) |
| Política de cobertura | `PASS` — linhas `>=90%`, branches `>=85%`, módulos mensuráveis `>=30%` |
| Compile, Flake8, Black, isort | `PASS` |
| mypy | `PASS` em `145 source files` |
| pip-audit | `PASS` — nenhuma vulnerabilidade conhecida; pacote local não publicado no PyPI permaneceu não auditável |
| Bandit | `PASS` em severidade alta |
| Stage 4B.5 | `PASS`; determinismo, benchmark e entrada inalterada passaram |
| Stage 9 | `PASS`; quatro workers, matriz de resoluções e DPI concluída |
| Runner legado formal | `ACCEPTED`; retorno histórico `1`, `exact=15`, `changed=11`, `missing=12`, `substitutes=42 tests` |
| Empacotamento Windows | `SUCCESS`; smoke em `11` checks; ZIP com `314` arquivos |
| Baseline staged | `PASS`; `3242` arquivos verificados por blob Git |
| Integridade de evidências | `PASS`; `134 manifests validated` com `--require-tracked --git-blob` |

## Proveniência do empacotamento

O build foi executado em checkout limpo do SHA do produto. O ZIP portátil
`NeoEng-D-Trace-0.3.0-win64-portable.zip` tem `124214125` bytes e SHA-256
`2e9df7157aa55411fabdd2336df30f3697a573c41748f18d972ab41dc6c345fd`.
O smoke validou CLI, projetos, exportações JSON/GLB, perfis Godot/Unity,
abertura/fechamento da GUI e diretório de estado do usuário.

O PyInstaller registrou o warning de hidden import `tzdata` ausente; o build
e o smoke concluíram com sucesso, portanto o warning permanece como limitação
registrada e não como sucesso silencioso.

## Runner legado e fronteira de decisão

O runner formal foi executado em checkout limpo do SHA `6ede2f6…`. O retorno
histórico `1` e as divergências `15/11/12` foram preservados nos snapshots;
os `42` testes substitutos passaram e o gate agregado aceitou o contrato.
Executar esse runner no checkout staged falha a pré-condição de limpeza da
árvore, por isso essa execução foi separada sem promover uma falha operacional
em resultado funcional.

O estado atual é aprovado localmente, mas não é encerramento global: C13 só
será decidido após push, abertura da PR sem merge e análise dos jobs remotos.
Não há autorização para merge, tag ou release nesta etapa.
