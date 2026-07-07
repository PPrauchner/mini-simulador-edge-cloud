# Log de Sessão — Grill with Docs (auditoria de cobertura)

**Projeto:** Mini-Simulador: Alocação de Tarefas em Edge-Cloud (Desafio técnico para bolsa — AI Horizon Labs)
**Data de início:** 2026-07-07 13:35 (sessão 2 — mesma data da sessão 1)
**Fonte da sessão:** auditoria dos artefatos produzidos na sessão 1 —
`CONTEXT.md`, `docs/adr/0001-…`, `docs/grills_logs/2026-07-07_grill-mini-simulador-edge-cloud.md`,
`docs/PRD.md`, `.claude/rules/code-conventions.md` —
contra as fontes originais (`docs/bolsa.jpeg` + `docs/transcricao_audios.md`).

> Este arquivo é atualizado a cada iteração da sessão. A numeração das perguntas
> continua a da sessão 1 (que terminou na Q8).

---

## Resultado da auditoria

**Fontes (brief + áudios) 100% cobertas** pelos artefatos da sessão 1; Q1–Q8,
CONTEXT.md, ADR-0001 e PRD consistentes entre si. Lacunas encontradas — decisões
que os documentos *usam* mas nunca cravaram:

1. **Semântica operacional da latência** — consome tempo simulado ou é contábil? (→ Q9)
2. **`--ticks` vs. invariante "toda Task chega a DONE"** — conflito de terminação. (→ Q10)
3. **Progresso no mesmo Tick** — Task alocada em `t` decrementa duração em `t`? (→ Q11)
4. **Termos de métrica fora do glossário** — Tempo de Resposta, Espera, Makespan,
   Utilização não estão no CONTEXT.md. (→ Q12)
5. **"Fila" sobrecarregada** — "sem fila no MVP" (infra) vs. "contenção = esperar na
   fila" (domínio) usam a mesma palavra para conceitos opostos. (→ Q13)

Menores (podem ser resolvidos na implementação): desempate determinístico do
LeastLoaded; Task com `demand` maior que a capacidade de qualquer Server.

---

## Perguntas e Respostas

### Q9 — A latência consome tempo simulado ou é puramente contábil?

Duas leituras de `resposta = espera + latência + duração`:
(a) **contábil** — Task alocada no tick `t` ocupa o Server de `t` até `t + duração`;
a latência só entra na soma da métrica; (b) **trânsito simulado** — a execução só
começa em `t + latência`, exigindo um estado novo no ciclo de vida (quebraria o
`PENDING → RUNNING → DONE` travado na Q3) e uma política de reserva de capacidade
durante o trânsito.

**Recomendação:** (a) contábil — preserva o ciclo de 3 estados, mantém os testes
calculáveis à mão, e o custo da latência já aparece na métrica que compara as
estratégias (o que o desafio avalia). (b) fica como evolução pós-MVP.

**Resposta do usuário:** concorda com (a); pediu este novo log de decisões em
`docs/grills_logs/`.

**Decidido:** latência é **contábil** — não consome Ticks simulados nem atrasa o
início da execução; entra apenas na soma do tempo de resposta. "Trânsito simulado"
registrado como Out of Scope no PRD.

---

### Q10 — O que `--ticks` significa, dado o invariante "toda Task chega a DONE"?

Os documentos pediam as duas coisas: CLI com `--ticks` e teste garantindo que toda
Task conclui. Opções: (a) `--ticks` = horizonte fixo (trunca e envia métricas
enviesadas — Tasks lentas somem do denominador); (b) rodar até todas DONE, sem teto
(cenário mal formado vira loop infinito); (c) rodar até todas DONE com `--ticks`
como **teto de segurança** — se estourar, falha com mensagem clara, sem reportar
métricas parciais como completas; mais validação **fail-fast** no carregamento do
Scenario (Task com `demand` que não cabe em Server nenhum → erro antes de simular).

**Recomendação:** (c) — comparação justa exige que toda estratégia veja a mesma
carga completa; o teto elimina o loop infinito; o fail-fast mata o caso patológico
na entrada. `--ticks` opcional com default generoso (ex.: 10.000).

**Resposta do usuário:** "sim".

**Decidido:** terminação natural (todas DONE); `--ticks` = teto de segurança
opcional que **falha** ao estourar; validação fail-fast de `demand` vs. capacidades
no carregamento do Scenario. Isso também resolve o item menor "Task impossível de
alocar" da auditoria.

---

### Q11 — Task alocada no tick `t` já progride nesse mesmo tick?

O loop da Q3 (`chegadas → alocação → progresso → métricas`) permitia duas leituras:
(a) a Task alocada em `t` é RUNNING quando a etapa de progresso roda e decrementa
duração já em `t` — `duration=3` alocada no tick 0 executa em 0,1,2 e está DONE ao
fim do tick 2; (b) só decrementa a partir de `t+1`, exigindo marcar recém-alocadas
para pular o progresso e criando um tick "morto" segurando capacidade sem executar.

**Recomendação:** (a) — leitura natural da ordem do loop, sem caso especial no
motor, aritmética limpa: alocada em `t` com duração `d` libera ao fim de `t+d−1`;
`espera = tick_da_alocação − arrival`; `resposta = espera + latência + d`.

**Resposta do usuário:** "a".

**Decidido:** progresso no mesmo tick da alocação. Fórmulas acima são o contrato
para os testes calculados à mão.

---

### Q12 — Definições canônicas das métricas no glossário

As cinco métricas não estavam no CONTEXT.md e três tinham ambiguidade real
(makespan inclui latência? utilização média sobre qual janela? split ponderado?).

**Recomendação:** cravar — **Espera** = Ticks em `PENDING` (`tick_da_alocação −
arrival`); **Tempo de Resposta** = espera + latência + duração; **Makespan** = Tick
da última `DONE`, latência fora (consistente com Q9); **Utilização** = média por
Tick de `demanda ocupada ÷ capacity`, do tick 0 ao makespan; **Split Edge×Cloud** =
fração das Tasks por **contagem**. Adicionar ao CONTEXT.md os quatro termos novos
(Wait, Response Time, Makespan, Utilization); o split vive na definição do Monitor.

**Resposta do usuário:** "concordo".

**Decidido:** definições acima são canônicas. CONTEXT.md atualizado (4 termos novos
+ split na definição do Monitor); PRD com as janelas na seção `monitor`.

---

### Q13 — Desfazer a sobrecarga da palavra "fila"

"Fila" era usada para dois conceitos opostos: a **fila de espera** de Tasks
`PENDING` (domínio, FIFO — existe e é central, decisão Q3) e a **fila de
processamento / mensagens** (infra — não existe no MVP). O code-conventions dizia
"sem fila de processamento" e o PRD "sem fila"; um leitor poderia cortar a fila errada.

**Recomendação:** corrigir a redação nos dois documentos distinguindo os termos;
sem entrada nova no glossário (a fila de espera já está implícita em Wait e
Placement Strategy).

**Resposta do usuário:** "concordo".

**Decidido:** code-conventions.md e PRD reescritos — "sem fila de mensagens /
processamento assíncrono (infra); a fila de espera de Tasks PENDING (domínio,
FIFO) existe".

---

### Itens menores — resolvidos por convenção (sem pergunta)

- **Desempate do LeastLoaded** (e de qualquer estratégia): em empate, vence o
  **primeiro Server na ordem declarada do Scenario** — estável e determinístico,
  sem aleatoriedade. Documentar na docstring da estratégia.
- **Task impossível de alocar**: já resolvido pela validação fail-fast da Q10.

---

### Q14 (fechamento) — A decisão da latência contábil (Q9) merece um ADR?

Das decisões desta sessão, só a Q9 passa nos três critérios de ADR: difícil de
reverter (muda o timing do motor e todos os testes), surpreendente sem contexto
(o avaliador pode ler a chegada instantânea na nuvem como bug) e trade-off real
(realismo vs. ciclo de 3 estados). Q10–Q13 são consequências ou correções de
redação — PRD e este log bastam.

**Recomendação:** criar o **ADR-0002 — Latência contábil, não trânsito simulado**;
o README de análise pode linká-lo (joga a favor de "capacidade de análise").

**Resposta do usuário:** "cria".

**Decidido:** criado `docs/adr/0002-latencia-contabil-nao-transito-simulado.md`.

---

## Estado dos artefatos (atualizado a cada decisão)

- **Q9** → PRD: nota de latência contábil na seção `engine` + item novo em Out of Scope.
- **Q10** → PRD: semântica de terminação e do `--ticks` na seção `engine`/CLI +
  validação fail-fast do Scenario.
- **Q11** → PRD: progresso no mesmo tick da alocação, com as fórmulas de contrato,
  na etapa 3 do loop do `engine`.
- **Q12** → CONTEXT.md: termos Wait, Response Time, Makespan, Utilization + split
  Edge×Cloud na definição do Monitor. PRD: janelas das métricas na seção `monitor`.
- **Q13** → code-conventions.md e PRD: redação das restrições distingue fila de
  mensagens (infra, fora) de fila de espera (domínio, dentro).
- **Q14** → `docs/adr/0002-latencia-contabil-nao-transito-simulado.md` criado.

---

## Fechamento da sessão

Auditoria concluída: fontes 100% cobertas, as 5 lacunas viraram Q9–Q14 (todas
decididas e propagadas para CONTEXT.md / PRD / code-conventions / ADR-0002) e os
itens menores foram resolvidos por convenção. O PRD em `docs/PRD.md` segue como
fonte para a implementação.
