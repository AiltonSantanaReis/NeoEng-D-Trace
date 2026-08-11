# Evidência corretiva — Etapa 10: cobertura pós-merge

## Identificação

- PR funcional: `#42`.
- Merge: `9b22bdc54b13992658172d4748bfab44f3127c8e`.
- CI pós-merge auditado: `31463873481`.
- Jobs: Linux `93692633942`; Windows `93692634029`.
- Artefato Linux: `9090792550`, SHA-256
  `9997d3c4f9affb283c8b21e9f637c4aa29232f479bc06505fbec306f81f23756`.
- Artefato Windows: `9090816311`, SHA-256
  `57497b3ae35f37a2311d73f2cafc629c2b8e93854cf42338ca0c2a941851687b`.

## Resultado rejeitado

Os dois jobs terminaram com `success`, mas o run não foi aceito somente pelo
estado verde. A inspeção dos XMLs de cobertura encontrou resultados diferentes
para o mesmo merge:

| Sistema | Linhas | Branches | Combinada |
|---|---:|---:|---:|
| Linux | `8.581/11.634` (`73,76%`) | `2.145/3.706` (`57,88%`) | `69,92%` |
| Windows | `8.582/11.634` (`73,77%`) | `2.146/3.706` (`57,91%`) | `69,93%` |

A diferença foi localizada em `src/collision/manager.py`: no Linux, a condição
da linha `147` cobriu `1/2` branches e a troca da linha `148` não executou; no
Windows e nos runs pré-merge, ambas executaram.

## Causa-raiz e correção

`UniformGridBroadPhase.get_all_pairs()` deriva pares de conjuntos. A API pública
já normaliza e ordena o resultado por ordem de registro, portanto não houve
divergência funcional. Porém, a cobertura do ramo de normalização dependia da
ordem não contratual produzida pelo conjunto.

O teste
`test_manager_normalizes_reverse_broadphase_pair_order` força explicitamente o
par inverso e comprova a normalização sem depender de plataforma ou hash seed.

## Validação local após a correção

- suíte canônica: `730 passed`;
- linhas: `8.582/11.634` (`73,77%`);
- branches: `2.146/3.706` (`57,91%`);
- cobertura combinada: `69,93%`;
- baseline: `300` arquivos;
- Etapa 10 integrada, mas encerramento pós-merge ainda não aprovado;
- PR corretiva, CI remoto, merge corretivo e novo CI pós-merge: pendentes;
- release: **NÃO APROVADA**.
