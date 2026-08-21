# Encerramento pós-merge — Etapa 2 da Interface Moderna Profissional

## Identificação

- PR funcional: #133.
- Merge SHA: ff66ffda11258499ab968916fc03827d66da1d87.
- Commit de implementação anterior: 0bb0477f9da6e1bdcde8d0961d1591339b13c01e.
- CI da PR: run 32536763488.
- Linux: job 96939047336, SUCCESS.
- Windows: job 96939047167, SUCCESS.
- Base validada localmente: main sincronizado com origin/main no merge SHA.
- Decisão: APROVADO no escopo da Etapa 2; não é aprovação de release.

## Escopo encerrado

A Etapa 2 entregou:

- biblioteca interna de 25 ícones SVG determinísticos, embutidos e sem caminhos locais;
- ações Open, Open Image, Save, Save As, Export, Export Collision, Fit View, 1:1 Pixel, Lit, X-Ray 1/2/3, Gizmo, Focus, Clean All e Language;
- ícones para as nove ferramentas da paleta existente;
- tooltips, nomes acessíveis, textos preservados e fallback textual negativo;
- atalhos reais F, X, A, 1–6, Ctrl+K, Ctrl+Z e Ctrl+Y preservados;
- configuração centralizada sem ultrapassar o limite estrutural do main_window.py;
- auditoria reprodutível de capturas reais nas três resoluções.

Ficam fora do encerramento: migração estrutural da barra esquerda, redesign do viewport, painéis laterais, editor de cenário separado, gizmo novo e as etapas 3–14.

## Validação pós-merge

Executado no main no merge SHA informado:

- baseline Git-blob: PASS, 1956 files;
- integridade de evidências Git-blob: PASS, 86 manifests;
- suíte integral: 1586 passed, 2 skipped, 0 failed;
- git diff --exit-code: PASS para arquivos rastreados;
- os cinco diretórios release-stage9-* untracked foram preservados e não fazem parte do merge;
- não houve force push, bypass, alteração de regra, remoção de teste ou reescrita de snapshot.

A captura/auditoria visual foi produzida antes do merge no commit de implementação e permanece byte-a-byte vinculada pelo manifesto e pelos hashes versionados. O pós-merge revalidou a integridade desses bytes; não foi declarada uma nova captura visual como se tivesse sido executada no main.

## Limitações declaradas

- Execução visual local em Windows com Qt offscreen; os jobs CI Linux/Windows cobriram os gates automatizados do repositório.
- Inspeção humana independente das imagens: NÃO TESTADA. A auditoria automatizada retornou PASS e zero achados; nenhuma qualidade estética subjetiva foi convertida em aprovação automática.
- Os dois skips da suíte são históricos e permaneceram explícitos.

## Estado final

A Etapa 2 da Interface Moderna Profissional está formalmente APROVADA somente no escopo acima. A próxima etapa correta do plano vivo é a Etapa 3 — Barra esquerda de ferramentas, após nova leitura das governanças e novo baseline específico.