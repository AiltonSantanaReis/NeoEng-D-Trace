# Etapa 0.5.1 — Relatório de captura forense

Data da captura: 27 de julho de 2026.

## 1. Objetivo

Congelar o estado técnico recebido antes de limpeza, renomeação, refatoração,
modernização ou criação do novo repositório.

Esta etapa não declara o código pronto e não autoriza exclusões. Seu objetivo é
garantir recuperação, rastreabilidade e uma base verificável para a Política de
Não Regressão.

## 2. Fontes de verdade preservadas

Foram consideradas:

- o ZIP original do projeto;
- o repositório Git contido no ZIP;
- a captura produzida no Windows após a Etapa 0 e a Política de Não Regressão;
- o bundle Git completo;
- o manifesto SHA-256;
- o estado de dependências do ambiente Python 3.11;
- os testes atuais e os testes recuperados do histórico.

Arquivos compilados, caches e logs são evidência histórica, não fonte de verdade
do comportamento.

## 3. Integridade da captura

A captura contém os 25 artefatos planejados:

1. status Git resumido;
2. status Git completo;
3. raiz do repositório;
4. branch atual;
5. commit HEAD;
6. remotes;
7. branches;
8. tags;
9. histórico;
10. arquivos rastreados;
11. arquivos excluídos;
12. arquivos modificados;
13. arquivos não rastreados;
14. estatística do diff;
15. numstat;
16. patch da árvore de trabalho;
17. patch do index;
18. configuração Git;
19. Python do sistema;
20. Python da `.venv`;
21. `pip freeze`;
22. `pip check`;
23. bundle Git;
24. validação do bundle;
25. manifesto SHA-256.

O ZIP foi testado e não apresentou erro de compressão.

O bundle foi verificado pelo Git e registra histórico completo.

## 4. Estado Git confirmado

- branch atual: `feature/physics-ui`;
- HEAD: `cf749564ab5d961772d66dc363d0e990cebf8da3`;
- remotes configurados: nenhum;
- arquivos rastreados no HEAD: 236;
- arquivos `.pyc` ou entradas de `__pycache__` rastreados: 145;
- tags preservadas:
  - `checkpoint/auto-detect-basic-20251128140647`;
  - `pre/auto-detect-20251128140435`;
  - `pre/auto-detect-perfect-20251128`.

## 5. Topologia das branches

Todas as branches registradas são ancestrais da branch atual. Não foi encontrada
divergência paralela a ser mesclada.

Isso significa que as branches funcionam como marcos históricos de uma evolução
linear e podem ser preservadas como referências até a criação do baseline.

Algumas referências apontam para o mesmo commit:

- `feature/auto-detect` e `feature/auto-detect-perfect`;
- `feature/physics-broadphase` e `feature/physics-convex-decomp`.

Nenhuma branch deverá ser apagada antes da criação do novo repositório e da
validação do bundle restaurado.

## 6. Árvore de trabalho capturada

Depois da aplicação da Etapa 0 e da Política de Não Regressão, o status visível
continha 264 entradas:

- 121 modificadas;
- 104 excluídas;
- 39 não rastreadas.

O número é menor que o inventário inicial porque o novo `.gitignore` passou a
ocultar `.venv`, backups, caches e outros artefatos. Isso não significa que os
arquivos desapareceram do ZIP original.

O diff rastreado continha:

- 225 entradas;
- 139 arquivos binários;
- 7.709 linhas adicionadas;
- 10.095 linhas removidas.

Separação aproximada do diff textual:

- código em `src/`: 7.151 adições e 4.283 remoções;
- testes: 23 adições e 3.890 remoções;
- código Python na raiz: 232 adições e 363 remoções;
- documentação/artefatos: 283 adições e 1.299 remoções.

Esses valores provam que o estado atual não é uma pequena correção sobre o HEAD.
Ele representa uma reconstrução substancial ainda não consolidada.

## 7. Ambiente Windows capturado

- Python do sistema usado na captura: 3.11.9;
- Python da `.venv`: 3.11.9;
- `pip check`: nenhuma dependência quebrada;
- PySide6: 6.10.1;
- NumPy: 2.2.6;
- OpenCV: 4.12.0.88;
- Pillow: 12.0.0;
- Pydantic: 2.12.5;
- Shapely: 2.1.2;
- pygltflib: 1.16.5;
- mapbox-earcut: 2.0.0.

O `pip freeze` é evidência do ambiente atual, mas ainda não é um lockfile de
distribuição.

## 8. Avisos de terminação de linha

O Git informou que alguns arquivos LF poderão ser convertidos para CRLF quando
forem tocados no Windows.

Esse aviso não indica falha na captura. Contudo, uma política de terminação de
linha deverá ser definida por `.gitattributes` antes do novo baseline para evitar
diffs artificiais.

Nenhum arquivo será normalizado automaticamente nesta fase.

## 9. Testes atuais confirmados no ambiente de auditoria

Foram reexecutados os testes não gráficos atuais:

- `tests/test_auto_detect.py`;
- `tests/test_broadphase_sap.py`;
- `tests/test_scene_repair.py`;
- `test_physics_core.py`.

Resultado: **17 aprovados**.

Ambiente: Linux, Python 3.13.5. Esse resultado não substitui a execução oficial
no Windows/Python 3.11.

## 10. Situação dos testes históricos

O HEAD rastreava 24 arquivos de teste com 196 testes detectáveis.

A árvore atual possui 36 testes detectáveis distribuídos em testes novos e um
teste remanescente modificado.

Isso não prova perda funcional automática, porque os novos testes podem testar
fluxos mais amplos. Entretanto, a redução impede remover os testes históricos
sem reavaliação.

Dos 113 testes históricos sem dependência direta de Qt:

- 100 foram executados;
- 92 passaram;
- 8 falharam;
- 13 não foram coletados por mudança na API SAT.

Os 83 testes históricos dependentes de Qt não foram executados no ambiente de
auditoria.

## 11. Conclusão da captura

A captura forense é válida e suficiente para reconstruir:

- todo o histórico Git;
- todas as branches e tags;
- o diff dos arquivos rastreados;
- o estado das dependências;
- a lista e o hash dos arquivos atuais não ignorados.

A Etapa 0.5 ainda não está concluída. Os próximos bloqueadores são:

1. preservar e reavaliar os testes históricos;
2. classificar os arquivos excluídos e não rastreados;
3. validar a suíte completa no Windows;
4. decidir expectativas incompatíveis;
5. criar o baseline em novo repositório privado;
6. somente depois remover artefatos do versionamento.
