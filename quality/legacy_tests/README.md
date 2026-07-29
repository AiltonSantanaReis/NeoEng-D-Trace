# Testes históricos preservados

Esta pasta contém cópias imutáveis dos testes rastreados no commit
`cf749564ab5d961772d66dc363d0e990cebf8da3` da branch `feature/physics-ui`.

## Finalidade

- preservar contratos e casos extremos encontrados no histórico;
- comparar o comportamento atual com versões anteriores;
- impedir exclusões silenciosas de cobertura;
- permitir a reconciliação gradual sem quebrar a suíte oficial em `tests/`.

## Regras

1. Não editar os arquivos em `tests/` diretamente.
2. Toda adaptação deve ser feita primeiro em uma cópia e relacionada ao teste de origem.
3. Um teste histórico somente poderá ser aposentado quando houver substituto equivalente,
   decisão documentada e evidência de execução.
4. Esta pasta não é coletada pelo `pytest.ini` principal do projeto.
5. O executor roda cada arquivo separadamente para que um erro de importação não esconda
   o resultado dos demais.

## Integridade

O arquivo `manifest.json` contém o commit, o blob Git e o SHA-256 normalizado para LF.
O executor valida os hashes antes de iniciar. A `.gitattributes` desta pasta marca os snapshots como binários apenas para impedir normalização de linha ou correções automáticas; os arquivos continuam sendo Python legível e executável.

## Execução no Windows

```powershell
.\tools\run_legacy_tests.ps1 -Group non-qt
.\tools\run_legacy_tests.ps1 -Group qt
.\tools\run_legacy_tests.ps1 -Group all
```

Também é possível usar diretamente:

```powershell
.\.venv\Scripts\python.exe .\tools\run_legacy_tests.py --group non-qt
```

Os relatórios são gravados por padrão em uma pasta temporária, fora do repositório.
