# Etapa 2 — colisores compostos no adaptador Unity

Status: **APROVADA**.

## Lacuna comprovada antes da implementação

O núcleo já exportava `shape_type: "compound"` e `parts` no contrato canônico de colisão. O adaptador Unity, porém, fixava `PolygonCollider2D.pathCount = 1`, calculava o fingerprint apenas do primeiro caminho e validava somente `GetPath(0)`. Portanto, colisores compostos eram reduzidos a um único caminho na integração Unity.

## Implementação aplicada

- O leitor Unity preserva o contrato canônico existente, inclusive `parts` como arrays de pontos, sem alterar o schema Python.
- Cada parte é validada, convertida de coordenadas de imagem para o espaço local do sprite e transformada para o eixo da Unity.
- O prefab gera `PolygonCollider2D.pathCount` igual ao número real de partes e grava cada caminho.
- O fingerprint inclui todos os caminhos, impedindo que uma alteração manual em uma parte secundária seja ignorada.
- A validação percorre todos os caminhos e seus respectivos números de pontos.
- O dry-run informa a mesma cardinalidade efetivamente usada no importador, inclusive quando existe override explícito.
- Colisores simples continuam usando um único caminho; manifests sem `collision` preservam o fallback histórico pelo polígono do sprite.

## Execução real no Unity

Versão detectada no computador: `6000.5.7f1`.

O harness criou um projeto Unity temporário e executou o pacote nativo sem substituir os artefatos do repositório. Os cenários comprovados foram:

| Cenário | Resultado observado |
|---|---|
| Manifesto com `shape_type=compound` e duas partes | 2 caminhos gerados |
| Cardinalidade dos caminhos | 4 pontos no primeiro e 4 no segundo |
| Mutação manual no segundo caminho seguida de alteração da imagem/hash | sincronização bloqueada |
| Preservação da mutação manual | confirmada |
| Saída final do runner | `UNITY_COMPOUND_STAGE2=PASS` |

## Evidências reproduzíveis

- Relatório: `docs/evidence/artifacts/native-compound-colliders-stage2-2026-08-17/stage2-unity-report.json`
- Log sanitizado: `docs/evidence/artifacts/native-compound-colliders-stage2-2026-08-17/unity-stage2-compound.log`
- Índice: `docs/evidence/artifacts/native-compound-colliders-stage2-2026-08-17/stage2-unity-index.json`
- Harness: `scripts/audit_unity_compound_colliders_stage2.py`
- Rerun final: `docs/evidence/artifacts/native-compound-colliders-stage2-rerun-2026-08-17/`

Hashes SHA-256 verificados independentemente com `Get-FileHash` na execução inicial:

- `stage2-unity-report.json`: `be841020ca4646430e18f7a5a050eb25ab947a0ae1a0b2701e5eaea6d1eb454f`
- `unity-stage2-compound.log`: `bfb4565b2c3c02b6280bf04453a5bb6a2d74d7336b5a056e646344e95f37cd57`

A execução final posterior à última alteração também passou independentemente:

- rerun `stage2-unity-report.json`: `1421e0259ef21452218551d459667ad8c24e4666a7dc17b20fdf3ff3e389115d`
- rerun `unity-stage2-compound.log`: `3e279647e7febb4f8bfbc89e6a294c5cda0706e6dad486c99fdae53bff631218`

A auditoria confirmou JSON válido, hashes correspondentes ao índice e ausência de padrões de identidade/processo não sanitizados. As saídas do Unity foram sanitizadas sem remover os marcadores de sucesso ou transformar falhas em sucesso.

## Regressão e limites declarados

- A Etapa 2 altera apenas o adaptador Unity e seus contratos de teste; não houve alteração no comportamento Godot.
- O override Unity existente continua representando um polígono único; quando aplicado explicitamente a um objeto composto, ele substitui o conjunto composto por esse override único. Isso é uma decisão de compatibilidade do contrato atual, não uma alegação de suporte a override composto.
- A transação global de múltiplos manifestos permanece na Etapa 4 e não foi antecipada.