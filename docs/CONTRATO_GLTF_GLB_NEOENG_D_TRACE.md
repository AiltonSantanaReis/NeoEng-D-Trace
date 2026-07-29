# Contrato GLTF/GLB preservado na árvore única

O exportador oficial reside em `src/exporters/gltf_exporter.py`.

Contratos preservados:

- `asset.generator = NeoEng-D-Trace GLTF Exporter`;
- GLB salvo preferencialmente por `GLTF2.save_binary()`;
- fallback `save()` somente para backends compatíveis sem `save_binary()`;
- retorno explícito `False` tratado como falha;
- escrita em temporário e substituição atômica;
- posições `float32`, índices `uint16`, accessors e bufferViews preservados;
- alinhamento do chunk BIN em quatro bytes;
- listas vazias de grupos podem ser omitidas pelo `pygltflib 1.16.5` após round-trip, equivalendo semanticamente a `groups: []`.

A consolidação muda apenas a localização interna do módulo. Não adiciona extrusão, UV, materiais ou 2.5D.
