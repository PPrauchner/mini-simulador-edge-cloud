# ADR-0001 — Interface de alocação em formato de lote com base gulosa

**Status:** aceito

## Contexto

O núcleo do desafio é a **decisão programática** de onde cada Task roda, com liberdade
para construir e **comparar diversas estratégias** de alocação. A forma da interface da
Placement Strategy determina quais classes de algoritmo são exprimíveis e é um dos pontos
mais avaliados ("clareza da lógica", "capacidade de análise").

## Decisão

A `PlacementStrategy` tem assinatura **em formato de lote**: recebe todas as Tasks
`PENDING` do tick e os Servers com sua capacidade livre atual + latência, e devolve as
alocações `list[(Task, Server | None)]` (`None` = esperar de propósito). Uma classe base
`GreedyStrategy` implementa o método de lote varrendo a fila em ordem FIFO e delegando a
um `place_one(task, servers)` por Task. O **motor valida a viabilidade** do conjunto
devolvido: compromete cada alocação se ainda couber no acumulado, senão a Task permanece
`PENDING`.

## Por quê

- **Estratégias simples ficam triviais:** menor-latência, borda-primeiro, round-robin
  herdam `GreedyStrategy` e escrevem só `place_one` — uma Task por vez.
- **Estratégias globais ficam possíveis:** uma estratégia pode sobrescrever o método de
  lote e fazer otimização/atribuição global, destravando a comparação analítica mais rica
  do projeto — *heurística gulosa vs. atribuição ótima*.
- O motor (não o algoritmo) é dono da invariante de capacidade, mantendo as estratégias curtas.

## Alternativas consideradas

- **Só por-tarefa** (`place(task, servers) -> Server | None`): mais simples, mas incapaz de
  exprimir otimização global — fecharia a porta para a comparação heurística×ótima.
- **Só lote, sem base gulosa:** até "mandar tudo pra nuvem" viraria um laço construindo um
  mapa, prejudicando a clareza das estratégias simples.

A base gulosa sobre uma interface de lote captura o lado bom de ambas ao custo de ~1 classe.
