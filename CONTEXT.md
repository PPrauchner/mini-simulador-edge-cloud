# Mini-Simulador: Alocação de Tarefas em Edge-Cloud

Simulador em tempo discreto (Python) que decide, de forma programática, em qual
servidor — de **borda** ou de **nuvem** — cada unidade de trabalho é executada, e
monitora o resultado para permitir comparar diferentes estratégias de alocação.

## Language

**Task** (pt: Tarefa):
A unidade de trabalho alocável — o objeto que um algoritmo posiciona em um Server
para ser executado. Nasce numa **origem** (um site de Edge, que determina a latência
até cada Server), tem uma demanda de capacidade e uma duração (em ticks); ocupa
capacidade do Server escolhido durante a duração e depois a libera. É o conceito
central do brief oficial.
_Avoid_: Application (para a unidade), Job, Process, Workload.

> Nota de evolução: no MVP, "Task" e "aplicação" (dos áudios) são o **mesmo** conceito.
> Se houver tempo, introduz-se **Application** como um conceito distinto — uma *fonte*
> que emite Tasks ao longo do tempo — e só então "Application" sai do _Avoid_ acima.

**Server** (pt: Servidor):
Um nó de execução que hospeda Tasks. Definido por uma **capacidade** (unidades de
computação disponíveis) e uma **latência** de rede para alcançá-lo. Existe em duas
variedades: Edge e Cloud.
_Avoid_: Host, Node, Máquina.

**Edge** (pt: Borda):
Variedade de Server próxima da origem das Tasks: **baixa latência**, **capacidade
pequena**. Representa também o site de borda (a estação radiobase é absorvida por ele,
não é entidade separada).
_Avoid_: Estação radiobase (como entidade), Fog.

**Cloud** (pt: Nuvem):
Variedade de Server distante da origem: **alta latência**, **capacidade grande**
(praticamente abundante). O contraste Edge×Cloud é o trade-off central do simulador.
_Avoid_: Datacenter, Central.

**Tick**:
A unidade de tempo discreto do simulador. O tempo avança um Tick por vez; toda a
dinâmica (chegada, alocação, execução, liberação de capacidade) acontece em Ticks.
_Avoid_: Passo, Ciclo, Step, Rodada.

**Placement Strategy** (pt: Estratégia de Alocação):
A política programável e substituível que decide em qual Server cada Task PENDING
é colocada. É o ponto de extensão central do simulador — construir e comparar
estratégias diferentes é o objetivo do projeto. Vê o estado atual (Tasks pendentes +
Servers com capacidade livre e latência) e devolve as alocações; o motor valida a
viabilidade. Ver ADR-0001.
_Avoid_: Scheduler, Alocador, Policy, Algoritmo (isolado).

**Placement** (pt: Alocação):
O ato de associar uma Task a um Server para execução. O resultado de uma decisão da
Placement Strategy que o motor considerou viável.
_Avoid_: Atribuição, Assignment, Escalonamento.

**Monitor** (pt: Monitor):
A estrutura de observação que coleta métricas da simulação para permitir **comparar
estratégias**: ocupação dos Servers por Tick e, por Task concluída, seus tempos de
espera/latência/execução. Inclui o **split Edge×Cloud**: a fração das Tasks (por
contagem) executada em cada variedade de Server. Não interfere na simulação —
apenas observa e agrega.
_Avoid_: Logger, Coletor, Profiler.

**Wait** (pt: Espera):
O tempo, em Ticks, que uma Task passa aguardando (`PENDING`) entre a chegada
(`arrival`) e a alocação a um Server. Chegar e ser alocada no mesmo Tick = espera
zero. É a métrica que revela contenção.
_Avoid_: Delay, Atraso, Queue time.

**Response Time** (pt: Tempo de Resposta):
O custo total de uma Task: **espera + latência + duração**. A latência é a do Server
escolhido, vista da origem da Task. É a métrica principal para comparar Placement
Strategies — numeriza o trade-off Edge×Cloud.
_Avoid_: Turnaround, Lead time, Tempo total.

**Makespan**:
O Tick em que a última Task do Scenario conclui (`DONE`) — o horizonte de execução
da carga inteira. A latência fica fora: ela é contábil e não estica a simulação.
_Avoid_: Duração total, Tempo de simulação.

**Utilization** (pt: Utilização):
A fração média da capacidade de um Server efetivamente ocupada por Tasks, medida
por Tick, do início da simulação até o Makespan.
_Avoid_: Ocupação (como métrica), Load, Carga.

**Scenario** (pt: Cenário):
Uma configuração reprodutível de infraestrutura (Servers com capacidade e latência) +
carga (lista de Tasks). É a **unidade de comparação**: rodar o mesmo Scenario com cada
Placement Strategy é o que torna a comparação justa. Determinístico dada uma `seed`.
_Avoid_: Caso, Config, Setup, Instância.
