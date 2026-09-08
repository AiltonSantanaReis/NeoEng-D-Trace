# Requalificação de symlink — tentativa no SHA `5a6275f`

**Data:** 2026-09-08  
**Escopo:** E00 / requalificação final-source, sem aceite de produto  
**Fonte:** `5a6275f8ef050abbc28c98726acd879ade37fa86`  
**Pacote de entrada:** `artifacts/sandbox-preparation-5a6275f8-20260908/`  
**SHA do ZIP de fontes:** `1615FAF2EBE90865DA8555EC17684A9BD24B823E1CAB88649BC3E96A60078B73`  
**SHA do `.wsb`:** `AECC21F052F55CEA87B63B6AA87590AA6F61A269E815907CB47714A123E0C168`

## Resultado observado

O `WindowsSandbox.exe` foi iniciado com o arquivo `NeoEng-Validacao.wsb`, usando
uma pasta de entrada somente leitura e uma pasta de evidências separada. O
processo terminou com código `0` após a janela de observação, mas a pasta de
evidências permaneceu sem `report.json`, `junit.xml` ou logs de teste.

O pacote não usa `LogonCommand`: a execução do script dentro do Sandbox exige
uma ação manual na sessão. Portanto, os 31 casos não foram executados nesta
tentativa e nenhum PASS foi inferido.

## Classificação normativa

- Requalificação do SHA final: `PENDING_EVIDENCE`.
- Resultado histórico em `35727d9`: permanece `PASS_SANDBOX_DIAGNOSTIC_ONLY` e
  não é transferido para este SHA.
- Suite local: `SKIP_PRIVILEGE_LIMITATION`, preservada como distinta.
- Próxima ação: executar manualmente o script dentro do Sandbox e preservar o
  relatório completo; não iniciar E01 enquanto E00 permanecer aberta.
