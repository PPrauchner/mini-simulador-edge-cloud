# ADR-0002 — Latência contábil, não trânsito simulado

**Status:** aceito

## Contexto

O tempo de resposta de uma Task é `espera + latência + duração` (sessão 1, Q3).
Restava a semântica operacional da latência no motor de tempo discreto: ela
**consome Ticks simulados** (a Task "viaja" até o Server antes de executar) ou é
**puramente contábil** (entra só na soma da métrica)? A escolha afeta o ciclo de
vida da Task, o makespan e todos os testes calculados à mão. Quem lê o código sem
este contexto pode ver uma Task "chegando" na nuvem instantaneamente e achar que é
um bug — foi uma escolha deliberada.

## Decisão

A latência é **contábil**. Uma Task alocada no tick `t` ocupa o Server desde `t` e
executa de `t` a `t + duração − 1`; a latência não atrasa o início da execução nem
estica a simulação — entra apenas na soma do tempo de resposta:
`resposta = (t_alocação − arrival) + latência + duração`. O makespan, portanto,
não inclui latência.

## Por quê

- **Preserva o ciclo de vida de 3 estados** (`PENDING → RUNNING → DONE`): trânsito
  simulado exigiria um quarto estado (nem pendente, nem executando) e uma política
  de reserva de capacidade durante a viagem.
- **Testes calculáveis à mão**: os invariantes do motor e os casos do Monitor são
  verificáveis com aritmética simples, sem simular viagem.
- **O trade-off Edge×Cloud continua visível onde importa**: na métrica que compara
  as estratégias — AllCloud paga a latência alta em toda resposta; o custo da
  distância aparece na tabela comparativa, que é o que o desafio avalia
  ("capacidade de análise").

## Alternativas consideradas

- **Trânsito simulado** (execução começa em `t + latência`): mais realista — a
  distância pesaria também no makespan e na ocupação, não só na resposta — mas
  exige o estado de trânsito no ciclo de vida e a decisão sobre reserva de
  capacidade durante a viagem. Registrado como evolução pós-MVP (Out of Scope no
  PRD); se adotado, este ADR deve ser substituído.
