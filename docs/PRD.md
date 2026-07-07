# PRD — Mini-Simulador: Alocação de Tarefas em Edge-Cloud

Status: ready-for-agent

> Fonte: sessões de *grill with docs* de 2026-07-07
> (`docs/grills_logs/2026-07-07_grill-mini-simulador-edge-cloud.md` e
> `docs/grills_logs/2026-07-07_grill-auditoria-cobertura.md`).
> Vocabulário conforme `CONTEXT.md`; decisões de arquitetura em `docs/adr/`.
> Prazo do desafio: **07/07/2026 23h59**.

---

## Problem Statement

Como pesquisador de infraestrutura edge-cloud, preciso decidir **onde executar tarefas**
— num servidor de borda (baixa latência, pouca capacidade) ou na nuvem (alta latência,
capacidade abundante) — mas não tenho nenhuma forma controlada de **experimentar e comparar
diferentes algoritmos de alocação**. Sem um ambiente reprodutível, não consigo saber qual
estratégia se sai melhor sob uma dada carga, nem enxergar o trade-off entre latência e
contenção ao longo do tempo.

## Solution

Um **mini-simulador em Python, em tempo discreto**, dirigido por uma CLI, no qual:

- a **infraestrutura** (Servers de Edge e Cloud) e a **carga** (Tasks) são modeladas
  como um **Scenario** reprodutível;
- a decisão de **qual Task vai em qual Server** é tomada por uma **Placement Strategy**
  programável e substituível — dá para escrever várias e trocá-las sem tocar no motor;
- um **Monitor** coleta métricas ao longo dos Ticks, permitindo **rodar o mesmo Scenario
  com cada estratégia e compará-las** lado a lado.

O produto entrega um repositório público e um vídeo explicativo, com o README trazendo a
**análise** dos resultados da comparação.

## User Stories

1. Como pesquisador, quero modelar Servers de **Edge** e **Cloud** com capacidade e
   latência distintas, para representar o trade-off central "borda rápida porém limitada
   vs. nuvem folgada porém distante".
2. Como pesquisador, quero modelar **Tasks** com origem, demanda de capacidade e duração,
   para representar unidades de trabalho realistas.
3. Como pesquisador, quero que cada Task tenha um **tick de chegada** (`arrival`), para que
   a carga varie ao longo do tempo e gere contenção dinâmica.
4. Como pesquisador, quero que o simulador avance em **tempo discreto (Ticks)**, para que
   a dinâmica de ocupação e liberação de capacidade seja observável passo a passo.
5. Como pesquisador, quero que uma Task ocupe capacidade de um Server pela sua **duração** e
   depois libere, para que a simulação capture fila e contenção, não só uma atribuição única.
6. Como pesquisador, quero que uma Task sem Server disponível **espere na fila** (permaneça
   `PENDING`) e seja reavaliada no próximo Tick, para medir o tempo de espera sob carga.
7. Como pesquisador, quero acompanhar o ciclo de vida da Task (`PENDING → RUNNING → DONE`),
   para entender em que estágio cada trabalho está a cada Tick.
8. Como pesquisador, quero que o **tempo de resposta** de uma Task seja
   `espera + latência + duração`, para numerizar o custo da escolha de Server.
9. Como autor de algoritmos, quero uma **interface de Placement Strategy** clara, para
   escrever diferentes estratégias sem mexer no motor.
10. Como autor de algoritmos, quero uma **estratégia gulosa por Task** de escrita trivial
    (herdar `GreedyStrategy`, implementar `place_one`), para prototipar políticas rápido.
11. Como autor de algoritmos, quero poder **sobrescrever a decisão em lote** (ver todas as
    Tasks pendentes de uma vez), para escrever estratégias de otimização global.
12. Como pesquisador, quero uma estratégia **AllCloud** (baseline), para ter um ponto de
    comparação de latência uniforme sem contenção.
13. Como pesquisador, quero uma estratégia **EdgeFirst** (borda local, senão nuvem), para
    ver a política intuitiva e como a borda satura sob carga.
14. Como pesquisador, quero uma estratégia **LeastLoaded** (Server com mais folga), para
    ver o efeito de balancear carga, inclusive usando a borda vizinha.
15. Como pesquisador, quero uma **estrutura de monitoramento** que colete métricas sem
    interferir na simulação, para comparar estratégias de forma justa.
16. Como pesquisador, quero as métricas: **tempo de resposta médio, tempo de espera médio,
    distribuição borda×nuvem, utilização média por Server e makespan**, para avaliar cada
    estratégia por vários ângulos.
17. Como pesquisador, quero **rodar o mesmo Scenario com cada estratégia** e ver uma
    **tabela comparativa** no console, para decidir qual é melhor sob aquela carga.
18. Como usuário da ferramenta, quero uma **CLI** que aceite `--scenario`, `--seed`,
    `--strategy`/`--compare` e `--ticks`, para configurar experimentos sem editar código.
19. Como usuário da ferramenta, quero definir a **seed pela linha de comando**, para
    reproduzir exatamente um experimento sem tocar em arquivo.
20. Como pesquisador, quero cenários **determinísticos dada uma seed**, para que a comparação
    entre estratégias seja justa (todas veem a mesma carga).
21. Como pesquisador, quero **cenários parametrizados** (ex.: carga baixa e carga alta), para
    observar como o ranking das estratégias muda com a carga.
22. Como avaliador do projeto, quero um **README com seção de análise** interpretando os
    números, para julgar a "capacidade de análise".
23. Como avaliador do projeto, quero **código organizado** (um módulo por conceito) e
    **testes**, para julgar clareza e organização.
24. Como mantenedor, quero o **núcleo sem dependências externas** (`python -m sim` roda
    direto), para que qualquer avaliador execute sem instalar nada.

## Implementation Decisions

- **Pacote `sim/`, um módulo por conceito** (respeita "organização do código"):
  `model`, `engine`, `strategies`, `monitor`, `scenarios`, `report`, `__main__`.
- **`model`**: dataclasses tipadas.
  - `Task`: `arrival` (Tick), `origin` (site de Edge), `demand` (unidades de computação,
    default 1), `duration` (Ticks), e estado de ciclo de vida `PENDING → RUNNING → DONE`.
  - `Server`: variedade Edge ou Cloud, `capacity` (inteiro de unidades) e uma latência que
    depende da origem da Task (local `1` / borda vizinha `3` / nuvem `8`, configuráveis).
    Roda Tasks concorrentes enquanto Σ`demand` ≤ `capacity`.
  - `Scenario`: infraestrutura (Servers) + carga (lista de Tasks), reprodutível dada uma seed.
- **`engine`**: motor de **tempo discreto**. Loop de cada Tick `t`:
  1. **Chegadas**: Tasks com `arrival == t` entram em `PENDING`.
  2. **Alocação**: a `Placement Strategy` decide; o motor **valida a viabilidade** (compromete
     cada alocação se couber no acumulado, senão a Task continua `PENDING`).
  3. **Progresso**: Tasks `RUNNING` decrementam a duração restante; as que zeram viram `DONE`
     e liberam capacidade. Vale também para as alocadas **neste mesmo tick** (o progresso vem
     depois da alocação): Task alocada em `t` com duração `d` executa de `t` a `t+d−1`;
     `espera = tick_da_alocação − arrival`.
  4. **Métricas**: alimenta o `Monitor`.
  - Contrato de execução: `engine.run(scenario, strategy) -> resultado observado (Monitor)`.
  - `tempo de resposta = espera (Ticks em PENDING) + latência (até o Server) + duração`.
  - A latência é **contábil**: não consome Ticks simulados nem atrasa o início da
    execução — a Task alocada no tick `t` ocupa o Server desde `t`; a latência entra
    apenas na soma do tempo de resposta.
  - **Terminação**: a simulação roda até **toda Task chegar a `DONE`** (terminação
    natural). `--ticks` é um **teto de segurança** opcional (default generoso, ex.:
    10.000): se estourar, a execução **falha com mensagem clara** — nunca reporta
    métricas parciais como se fossem completas.
  - **Validação fail-fast** no carregamento do Scenario: Task com `demand` maior que
    a capacidade de qualquer Server → erro imediato, antes de simular.
- **`strategies`** (ver **ADR-0001**): interface **em formato de lote** com base gulosa.
  - `PlacementStrategy.place(pending, servers) -> list[(Task, Server | None)]`
    (`None` = esperar de propósito). Recebe as Tasks pendentes e os Servers com capacidade
    livre atual + latência-desde-a-origem.
  - `GreedyStrategy` implementa `place` varrendo a fila em ordem FIFO e delegando a
    `place_one(task, servers)`.
  - Catálogo do MVP: **AllCloud**, **EdgeFirst**, **LeastLoaded** (todas herdam `GreedyStrategy`).
- **`monitor`**: observador que registra ocupação por Server a cada Tick e, por Task concluída,
  espera/latência/duração; expõe os agregados (resposta média, espera média, split
  borda×nuvem, utilização média, makespan). Não interfere na simulação. Definições
  canônicas no `CONTEXT.md`: makespan = Tick da última `DONE` (latência fora);
  utilização média do tick 0 ao makespan; split por **contagem** de Tasks.
- **`scenarios`**: fábricas parametrizadas que retornam um `Scenario` a partir de `seed` e
  parâmetros de carga; ≥2 cenários (carga baixa / alta).
- **`report`**: monta a **tabela comparativa** (uma linha por estratégia) para o console.
- **`__main__`**: CLI (`argparse`) — `--scenario`, `--seed`, `--strategy`/`--compare`,
  `--ticks` (teto de segurança opcional) e parâmetros de carga; monta o Scenario,
  roda, imprime a tabela.
- **Restrições** (ver `.claude/rules/code-conventions.md`): Python 3.10+; **núcleo stdlib-only**
  (`argparse`, `dataclasses`, `statistics`); sem banco, sem **fila de mensagens** (a
  **fila de espera** de Tasks `PENDING` é conceito de domínio e existe), sem framework
  web/GUI; execução síncrona, um Scenario por vez; reprodutibilidade sempre por `seed` explícita.

## Testing Decisions

- **O que é um bom teste aqui**: exercita **comportamento externo**, não implementação.
  Entra um `Scenario` + uma `Placement Strategy` (ou um estado montado à mão); sai um
  resultado observável (métricas do `Monitor`, ou a decisão da estratégia). Nada de espiar
  contadores internos do motor ou métodos privados.
- **Seam 1 — integração (o mais alto), via `engine.run(scenario, strategy)`**: dado um
  Scenario conhecido e uma estratégia, o `Monitor` reporta as métricas esperadas. É o teste
  que mais se aproxima do uso real; preferir este para cobertura end-to-end.
- **Seam 2 — invariantes do motor, via `engine.run`**: (a) a capacidade de nenhum Server é
  excedida em nenhum Tick; (b) toda Task chega a `DONE`; (c) `resposta = espera + latência +
  duração` para um caso calculado à mão.
- **Seam 3 — estratégias, via `strategy.place(...)`**: sobre um estado montado à mão —
  AllCloud sempre escolhe a nuvem; EdgeFirst escolhe a borda local quando há folga e a nuvem
  quando não há; LeastLoaded escolhe o Server com mais capacidade livre.
- **Seam 4 — Monitor**: dada uma sequência conhecida de alocações/conclusões, os agregados
  (médias, split, makespan) batem com o valor calculado à mão.
- **Prior art**: greenfield — não há testes anteriores; estes tornam-se a referência.
  `tests/test_engine.py`, `tests/test_strategies.py`, `tests/test_monitor.py`.

## Out of Scope

- **GlobalOptimal** (estratégia em lote com otimização global) — esticada; e, quando feita,
  será uma **heurística global por Tick**, não um ótimo sobre todo o horizonte de tempo.
- **Gráfico `matplotlib`** (`--chart`) — extra opcional; núcleo permanece stdlib-only.
- **Loader de cenário YAML/JSON** — extra opcional; cenários vivem em Python no MVP.
- **"Leitura 2" — `Application` como gerador** que emite Tasks em runtime; no MVP a carga é
  uma lista fixa com `arrival`.
- **Segundo eixo de recurso** (ex.: memória) — decidido usar um único recurso escalar.
- **Rejeição de Tasks** (por espera máxima) — no MVP a contenção é tratada só por espera.
- **Latência como trânsito simulado** (execução começando em `t + latência`, com estado
  de trânsito no ciclo de vida) — no MVP a latência é contábil, só entra na métrica.
- **Estação radiobase como entidade** — absorvida pelo Server de borda.
- **Persistência, banco de dados, fila, interface web/GUI, concorrência real.**

## Further Notes

- **Prazo é hoje (07/07/2026 23h59)** — o escopo foi deliberadamente travado no MVP acima;
  os itens "Out of Scope" são explicitamente esticados.
- **Entregáveis do desafio**: repositório público no GitHub + **vídeo explicativo**. O README
  deve conter *como rodar* e a **seção de análise** dos resultados da comparação.
- **Mapa para os critérios de avaliação**: "clareza da lógica" → tick loop e estratégias
  simples/legíveis; "organização do código" → um módulo por conceito + testes; "capacidade de
  análise" → tabela comparativa + seção de análise no README.
- Glossário completo em `CONTEXT.md`; a interface de alocação e seus porquês em
  `docs/adr/0001-interface-de-alocacao-em-lote-com-base-gulosa.md`; a semântica
  contábil da latência em `docs/adr/0002-latencia-contabil-nao-transito-simulado.md`.
