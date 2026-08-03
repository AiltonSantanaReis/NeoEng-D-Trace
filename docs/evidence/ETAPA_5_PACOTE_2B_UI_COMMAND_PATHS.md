# Evidência — Etapa 5, Pacote 2B: caminhos de UI por comandos

## Base

- Commit da `main`: `5109ba0b03a4d075c73e5183c473b29d94bc7f5c`;
- Pacote 2A integrado pela PR `#17`;
- workflow pós-merge do Pacote 2A: `#60` (`30773877017`);
- evidência local pós-merge SHA-256:
  `de05fe691b00965f8d25260920530f8c281bb30065ad082e546bb242c8cf6758`;
- baseline inicial: `238` arquivos;
- risco relacionado: `R-004`.

## Objetivo

Eliminar fallbacks manuais nos caminhos de interface já cobertos pelos
comandos transacionais do Pacote 2A.

## Escopo

- SidePanel:
  - renomear;
  - excluir;
  - alternar colisão;
  - expandir e contrair;
  - inverter;
  - aplicar prévia;
- CanvasView:
  - excluir;
  - alternar colisão;
  - limpar cena;
- tratamento explícito de `APPLIED`, `NO_CHANGE`, `REJECTED` e `FAILED`;
- ausência de mutação quando o `CommandManager` não está disponível;
- prévia limpa de forma determinística ao aplicar ou cancelar;
- testes funcionais e inspeção estrutural dos caminhos incluídos.

## Fora do escopo

- movimento pelo gizmo;
- edição individual de vértices;
- criação manual de polígonos;
- camadas e grupos completos;
- Bézier;
- importação composta;
- migração integral das 117 mutações candidatas;
- metas finais de cobertura;
- encerramento de `R-004` ou da Etapa 5.

## Gates obrigatórios

- `7` testes específicos do Pacote 2B;
- suíte completa;
- Black, isort, Flake8 fatal e mypy;
- baseline de `240` arquivos;
- CI Linux e Windows;
- revisão integral do diff;
- validação manual posterior da interface.

## Decisão esperada

Aprovação somente no escopo do Pacote 2B. `R-004` permanece aberto.
